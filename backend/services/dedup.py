"""
Одну й ту саму квартиру власник часто виставляє одразу на кількох сайтах
(OLX + DOM.RIA — типова комбінація). Без дедуплікації стрічка дублюється,
що виглядає непрофесійно й дратує користувача. Тут — легка, безкоштовна
евристика: схожа адреса + близька ціна + той самий город + ті самі кімнати
в межах останніх N днів = вважаємо дублем і не додаємо повторно.

Fuzzy-збіг рядків через важку модель був би точнішим, але коштує грошей
(embeddings API) або CPU (локальна модель) — обидва варіанти проблемні для
безкоштовного Railway-тарифу. difflib з stdlib безкоштовний і "достатньо
хороший" для очевидних дублів; складні випадки (адреса вказана по-різному)
він пропустить — це свідомий компроміс, а не недогляд.
"""
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Listing

PRICE_TOLERANCE_PCT = 0.05   # 5% — оренда часто округлюється по-різному на різних сайтах
ADDRESS_SIMILARITY_THRESHOLD = 0.72
LOOKBACK_DAYS = 14  # дублі шукаємо лише серед недавніх оголошень — не варто звіряти з усією історією


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    return text.lower().replace("вул.", "").replace("вулиця", "").strip()


async def find_duplicate(db: AsyncSession, city: str, price: int, rooms: int | None, street: str | None) -> Listing | None:
    since = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)
    price_low, price_high = price * (1 - PRICE_TOLERANCE_PCT), price * (1 + PRICE_TOLERANCE_PCT)

    candidates = (await db.execute(
        select(Listing).where(
            Listing.city == city,
            Listing.price.between(price_low, price_high),
            Listing.created_at >= since,
        )
    )).scalars().all()

    normalized_street = _normalize(street)
    if not normalized_street:
        return None  # без адреси порівнювати за одною ціною надто ризиковано (false positive)

    for candidate in candidates:
        if rooms is not None and candidate.rooms is not None and candidate.rooms != rooms:
            continue
        similarity = SequenceMatcher(None, normalized_street, _normalize(candidate.street)).ratio()
        if similarity >= ADDRESS_SIMILARITY_THRESHOLD:
            return candidate

    return None

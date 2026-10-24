import asyncio
import math
import time
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import GeocodeCache
from config import settings

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim вимагає ідентифікований User-Agent і не більше 1 запиту/сек — це офіційна безкоштовна політика.
HEADERS = {"User-Agent": f"RentFinderApp/1.0 (contact: {settings.NOMINATIM_CONTACT_EMAIL})"}

_last_request_ts = 0.0
_MIN_INTERVAL = 1.1  # трохи більше секунди для запасу


async def _throttle():
    global _last_request_ts
    elapsed = time.monotonic() - _last_request_ts
    if elapsed < _MIN_INTERVAL:
        await asyncio.sleep(_MIN_INTERVAL - elapsed)
    _last_request_ts = time.monotonic()


async def geocode(db: AsyncSession, query: str) -> tuple[float, float] | None:
    """Повертає (lat, lon) для довільного текстового опису адреси/міста/вулиці.
    Результат кешується в БД, тому повторний скан не б'є по Nominatim знову."""
    if not query or not query.strip():
        return None

    normalized = query.strip().lower()
    cached = (await db.execute(
        select(GeocodeCache).where(GeocodeCache.query == normalized)
    )).scalar_one_or_none()
    if cached:
        if cached.latitude is None:
            return None  # раніше вже пробували й не знайшли — не повторюємо запит даремно
        return (cached.latitude, cached.longitude)

    await _throttle()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                NOMINATIM_URL,
                params={"q": query, "format": "json", "limit": 1, "countrycodes": "ua"},
                headers=HEADERS,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        return None

    if not data:
        db.add(GeocodeCache(query=normalized, latitude=None, longitude=None))
        await db.commit()
        return None

    lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
    db.add(GeocodeCache(query=normalized, latitude=lat, longitude=lon))
    await db.commit()
    return (lat, lon)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

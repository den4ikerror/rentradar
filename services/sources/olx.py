import httpx
from selectolax.parser import HTMLParser

from services.sources.base import SourceAdapter, SearchCriteria, ParsedListing
from services.sources.http_utils import get_with_retry, polite_delay

BASE_URL = "https://www.olx.ua/uk/nedvizhimost/kvartiry/dolgosrochnaya-arenda-kvartir"

CITY_SLUGS = {
    "Київ": "kiev",
    "Львів": "lvov",
    "Одеса": "odessa",
    "Харків": "kharkov",
    "Дніпро": "dnepr",
    "Запоріжжя": "zaporozhye",
    "Івано-Франківськ": "ivano-frankovsk",
    "Тернопіль": "ternopol",
    "Вінниця": "vinnitsa",
    "Полтава": "poltava",
    "Кривий Ріг": "kryvyi-rih",
    "Миколаїв": "nikolaev",
}

KNOWN_DISTRICTS = [
    "галицький", "шевченківський", "франківський", "сихівський", "личаківський", "залізничний",
    "печерський", "голосіївський", "подільський", "оболонський", "святошинський", "солом'янський", "дарницький", "дніпровський", "деснянський"
]

def extract_district(text: str) -> str | None:
    t_lower = text.lower()
    for d in KNOWN_DISTRICTS:
        if d in t_lower:
            return d.capitalize() + " р-н"
    return None


class OlxAdapter(SourceAdapter):
    name = "olx"

    async def search(self, criteria: SearchCriteria, max_pages: int = 3) -> list[ParsedListing]:
        city_slug = CITY_SLUGS.get(criteria.city, criteria.city.lower())
        url = f"{BASE_URL}/{city_slug}/"

        results: list[ParsedListing] = []
        seen: set[str] = set()

        async with httpx.AsyncClient() as client:
            for page in range(1, max_pages + 1):
                params = {"page": page} if page > 1 else None
                resp = await get_with_retry(client, url, params)
                if resp is None:
                    break

                tree = HTMLParser(resp.text)
                cards = tree.css("div[data-cy='l-card'], [data-testid='l-card'], article, .css-1sw7q4x")
                if not cards:
                    break

                for card in cards:
                    link_el = card.css_first("a[href*='/d/uk/obyavlenie/'], a[href*='/uk/d/'], a")
                    title_el = card.css_first("h4, h6, [data-cy='ad-card-title'], [class*='title']")
                    price_el = card.css_first("[data-testid='ad-price'], [class*='price']")
                    if not (link_el and title_el and price_el):
                        continue

                    href = link_el.attributes.get("href", "")
                    if not href:
                        continue
                    full_url = href if href.startswith("http") else f"https://www.olx.ua{href}"
                    if full_url in seen:
                        continue
                    seen.add(full_url)

                    raw_price = price_el.text(strip=True)
                    part = raw_price.split("{")[0].split("грн")[0].split(".")[0]
                    digits = "".join(c for c in part if c.isdigit())
                    price = int(digits) if digits and len(digits) < 8 else 0
                    if not price:
                        continue

                    img_el = card.css_first("img")
                    photo = img_el.attributes.get("src") or img_el.attributes.get("data-src") if img_el else None

                    location_el = card.css_first("[data-testid='location-date'], [class*='location']")
                    loc_text = location_el.text(strip=True) if location_el else ""
                    loc_clean = loc_text.split("-")[0]
                    parts = [p.strip() for p in loc_clean.split(",")]
                    street = parts[0] if len(parts) > 0 else None

                    card_text = card.text(separator=" ", strip=True)
                    district = extract_district(card_text) or (parts[1] if len(parts) > 1 else criteria.district)

                    results.append(ParsedListing(
                        source=self.name,
                        source_url=full_url,
                        title=title_el.text(strip=True),
                        price=price,
                        city=criteria.city,
                        district=district,
                        street=street,
                        rooms=criteria.rooms,
                        photos=[photo] if photo and photo.startswith("http") else [],
                    ))

                await polite_delay()

        return results

    async def fetch_details(self, url: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await get_with_retry(client, url)

        empty = {"description": "", "photos": [], "seller_type": "unknown", "area": None, "floor": None, "total_floors": None}
        if resp is None:
            return empty

        tree = HTMLParser(resp.text)

        description_el = tree.css_first("[data-cy='ad_description']")
        description = description_el.text(strip=True) if description_el else ""

        photos = []
        for img in tree.css("[data-testid='swiper-wrapper'] img, [data-testid='image-gallery-container'] img, img[src*='apollo.olxcdn.com']"):
            src = img.attributes.get("src") or img.attributes.get("data-src")
            if src and src not in photos and "s=" in src:
                photos.append(src)
        if not photos:
            for img in tree.css("img[src*='olxcdn.com']"):
                src = img.attributes.get("src") or img.attributes.get("data-src")
                if src and src not in photos:
                    photos.append(src)

        seller_el = tree.css_first("[data-testid='trader-title']")
        seller_type = "company" if seller_el else "private"

        area, floor, total_floors = None, None, None
        params_el = tree.css_first("[data-testid='ad-parameters-container']")
        if params_el:
            text = params_el.text(separator="|", strip=True).lower()
            for chunk in text.split("|"):
                if "поверх" in chunk and "поверхів" not in chunk:
                    digits = "".join(c for c in chunk if c.isdigit())
                    floor = int(digits) if digits else floor
                if "м²" in chunk:
                    digits = "".join(c for c in chunk if c.isdigit() or c == ".")
                    try:
                        area = float(digits)
                    except ValueError:
                        pass

        return {
            "description": description, "photos": photos or [], "seller_type": seller_type,
            "area": area, "floor": floor, "total_floors": total_floors,
        }

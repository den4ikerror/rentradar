import httpx
from selectolax.parser import HTMLParser

from services.sources.base import SourceAdapter, SearchCriteria, ParsedListing
from services.sources.http_utils import get_with_retry, polite_delay

BASE_URL = "https://rieltor.ua"

RIELTOR_CITY_SLUGS = {
    "Київ": "kiev",
    "Львів": "lvov",
    "Одеса": "odessa",
    "Харків": "harkov",
    "Дніпро": "dnepr",
    "Запоріжжя": "zaporozhye",
    "Івано-Франківськ": "ivano-frankovsk",
    "Тернопіль": "ternopol",
    "Вінниця": "vinnitsa",
    "Полтава": "poltava",
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


class RieltorAdapter(SourceAdapter):
    name = "rieltor"

    async def search(self, criteria: SearchCriteria, max_pages: int = 3) -> list[ParsedListing]:
        city_slug = RIELTOR_CITY_SLUGS.get(criteria.city, criteria.city.lower())
        url = f"{BASE_URL}/{city_slug}/flats-rent/"

        results: list[ParsedListing] = []
        seen: set[str] = set()

        async with httpx.AsyncClient() as client:
            for page in range(1, max_pages + 1):
                params = {"page": page} if page > 1 else None
                resp = await get_with_retry(client, url, params)
                if resp is None:
                    break

                tree = HTMLParser(resp.text)
                cards = tree.css("article, div[class*='realty'], div[class*='item'], div[class*='card']")
                if not cards:
                    break

                for card in cards:
                    link_el = card.css_first("a[href]")
                    price_el = card.css_first("[class*='price']")
                    if not (link_el and price_el):
                        continue

                    href = link_el.attributes.get("href", "")
                    if not href:
                        continue
                    full_url = href if href.startswith("http") else f"https://rieltor.ua{href}"
                    if full_url in seen:
                        continue
                    seen.add(full_url)

                    raw_price = price_el.text(strip=True).lower()
                    price_digits = "".join(ch for ch in raw_price if ch.isdigit())
                    price = int(price_digits) if price_digits else 0
                    if not price:
                        continue
                    if price < 3000 or "$" in raw_price or "usd" in raw_price or "у.о." in raw_price:
                        price = price * 41

                    card_text = card.text(separator=" ", strip=True)
                    district = extract_district(card_text) or criteria.district

                    street_el = card.css_first("[class*='address'], [class*='location']")
                    street = street_el.text(strip=True) if street_el else None

                    img_el = card.css_first("img")
                    photo = img_el.attributes.get("src") or img_el.attributes.get("data-src") if img_el else None

                    title_el = card.css_first("h3, h4, [class*='title']")
                    title = title_el.text(strip=True) if title_el else "Оренда квартири (Rieltor)"

                    results.append(ParsedListing(
                        source=self.name,
                        source_url=full_url,
                        title=title,
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
        description_el = tree.css_first("[class*='description'], div[class*='text']")
        description = description_el.text(strip=True) if description_el else ""

        photos = [img.attributes.get("src") for img in tree.css("img[src*='rieltor.ua'], [class*='gallery'] img") if img.attributes.get("src")]

        seller_el = tree.css_first("[class*='agency'], [class*='company'], [class*='seller']")
        seller_type = "company" if seller_el else "private"

        return {
            "description": description, "photos": photos or [], "seller_type": seller_type,
            "area": None, "floor": None, "total_floors": None,
        }

import httpx
from selectolax.parser import HTMLParser

from services.sources.base import SourceAdapter, SearchCriteria, ParsedListing
from services.sources.http_utils import get_with_retry, polite_delay

BASE_URL = "https://dom.ria.com/uk/arenda-kvartir"

DOMRIA_CITY_SLUGS = {
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


class DomRiaAdapter(SourceAdapter):
    name = "domria"

    async def search(self, criteria: SearchCriteria, max_pages: int = 3) -> list[ParsedListing]:
        city_slug = DOMRIA_CITY_SLUGS.get(criteria.city, criteria.city.lower())
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
                cards = tree.css("section.realty-item, div.realty-item, .realty-preview, article")
                if not cards:
                    break

                for card in cards:
                    link_el = card.css_first("div.tit a, a[href*='realty-'], a")
                    price_el = card.css_first("[data-tm='realty-full-price'], .size22 b, .price, [class*='price']")
                    if not (link_el and price_el):
                        continue

                    href = link_el.attributes.get("href", "")
                    if not href:
                        continue
                    full_url = href if href.startswith("http") else f"https://dom.ria.com{href}"
                    if full_url in seen:
                        continue
                    seen.add(full_url)

                    price_text = "".join(ch for ch in price_el.text() if ch.isdigit())
                    price = int(price_text) if price_text else 0
                    if not price:
                        continue

                    title_el = card.css_first("div.tit a, h3, h2, [class*='title']")
                    street_el = card.css_first(".item-address, [class*='address']")
                    img_el = card.css_first("img")
                    photo = img_el.attributes.get("src") or img_el.attributes.get("data-src") if img_el else None

                    loc_text = street_el.text(strip=True) if street_el else ""
                    parts = [p.strip() for p in loc_text.split(",")]
                    street = parts[0] if len(parts) > 0 else None

                    card_text = card.text(separator=" ", strip=True)
                    district = extract_district(card_text) or (parts[1] if len(parts) > 1 else criteria.district)

                    results.append(ParsedListing(
                        source=self.name,
                        source_url=full_url,
                        title=title_el.text(strip=True) if title_el else "Оренда квартири",
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
        description_el = tree.css_first(".description-text, [class*='description'], .read-more-text")
        description = description_el.text(strip=True) if description_el else ""

        photos = [img.attributes.get("src") for img in tree.css(".gallery img, .photo-74x56 img, [class*='gallery'] img, img[src*='ria.com']") if img.attributes.get("src")]

        seller_el = tree.css_first(".seller-info, .agency-name, [class*='seller']")
        seller_type = "company" if seller_el else "private"

        return {
            "description": description, "photos": photos or [], "seller_type": seller_type,
            "area": None, "floor": None, "total_floors": None,
        }

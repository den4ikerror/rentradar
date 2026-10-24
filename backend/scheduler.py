import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from datetime import datetime, timedelta

from config import settings
from database import async_session
from models import SearchFilter, Listing, User
from services.sources import ALL_SOURCES
from services.sources.base import SearchCriteria, ParsedListing
from services.anti_realtor import is_agency
from services.price_analytics import calc_price_deviation
from services.geocoding import geocode, haversine_km
from services.attribute_extraction import extract_attributes, passes_soft_filter
from services.dedup import find_duplicate


logger = logging.getLogger("rentfinder.scheduler")
scheduler = AsyncIOScheduler()

ACTIVE_SOURCES = [s for s in ALL_SOURCES if s.name in settings.ENABLED_SOURCES]


async def scan_all_filters():
    async with async_session() as db:
        now = datetime.utcnow()
        active_filters = (await db.execute(
            select(SearchFilter).where(SearchFilter.is_active == True)
        )).scalars().all()

        for f in active_filters:
            due = (
                f.last_scanned_at is None
                or now - f.last_scanned_at >= timedelta(minutes=f.scan_interval_minutes)
            )
            if not due:
                continue

            try:
                await _scan_single_filter(db, f)
            except Exception:
                logger.exception("Скан фільтра #%s (user_id=%s) впав з помилкою", f.id, f.user_id)
            finally:
                f.last_scanned_at = now
                await db.commit()


async def _ensure_street_coords(db, f: SearchFilter):
    if not f.street or not f.street_radius_km or f.street_lat is not None:
        return
    query = f"{f.street}, {f.city}, Україна"
    coords = await geocode(db, query)
    if coords:
        f.street_lat, f.street_lon = coords
        await db.commit()


async def _calc_geo_distance(db, f: SearchFilter, item) -> tuple[float | None, bool]:
    if not f.street or not f.street_radius_km or f.street_lat is None:
        return None, True

    lat, lon = item.latitude, item.longitude
    if lat is None or lon is None:
        search_target = item.street
        if not search_target or len(search_target) < 3:
            import re
            match = re.search(r'(вул\.?|вулиця|просп\.?|проспект|пл\.?|площа)\s+[А-Яа-яЇїІіЄєҐґ0-9\-\.\"]+', item.title, re.IGNORECASE)
            if match:
                search_target = match.group(0)

        if not search_target:
            return None, False

        address_query = f"{search_target}, {item.city}, Україна"
        coords = await geocode(db, address_query)
        if not coords:
            return None, False
        lat, lon = coords

    distance = haversine_km(f.street_lat, f.street_lon, lat, lon)
    distance_rounded = round(distance, 2)
    is_within = distance_rounded <= f.street_radius_km
    return distance_rounded, is_within


async def _scan_single_filter(db, f: SearchFilter):
    await _ensure_street_coords(db, f)

    room_variants = f.room_options if f.room_options else [None]
    new_count = 0
    duplicate_count = 0
    filtered_out_count = 0

    for rooms in room_variants:
        criteria = SearchCriteria(
            region=f.region, city=f.city, district=f.district,
            min_price=f.min_price, max_price=f.max_price, rooms=rooms,
            min_area=f.min_area, floor_not_first=f.floor_not_first,
            floor_not_last=f.floor_not_last, pets_allowed_only=f.pets_allowed_only,
            property_types=f.property_types or [], renovation_type=f.renovation_type,
            is_new_building=f.is_new_building, furnished_only=f.furnished_only,
            heating_type=f.heating_type, has_elevator=f.has_elevator,
            has_parking=f.has_parking, has_balcony=f.has_balcony,
            internet_included=f.internet_included, utilities_included=f.utilities_included,
            min_lease_months=f.min_lease_months, deposit_required=f.deposit_required,
        )
        added, dupes, filtered = await _scan_with_criteria(db, f, criteria)
        new_count += added
        duplicate_count += dupes
        filtered_out_count += filtered

    logger.info(
        "Фільтр #%s: додано %s, пропущено дублів %s, відсіяно за критеріями %s (джерел: %s, варіантів кімнат: %s)",
        f.id, new_count, duplicate_count, filtered_out_count, len(ACTIVE_SOURCES), len(room_variants),
    )


async def _scan_with_criteria(db, f: SearchFilter, criteria: SearchCriteria) -> tuple[int, int, int]:
    new_count = 0
    duplicate_count = 0
    filtered_out_count = 0

    for source in ACTIVE_SOURCES:
        try:
            raw_results = await source.search(criteria)
        except Exception:
            logger.warning("Джерело %s недоступне для фільтра #%s, пропускаємо", source.name, f.id, exc_info=True)
            raw_results = []

        logger.info("Фільтр #%s / %s: знайдено %s оголошень", f.id, source.name, len(raw_results))


        for item in raw_results:
            existing = (await db.execute(
                select(Listing).where(Listing.source_url == item.source_url)
            )).scalar_one_or_none()
            if existing:
                continue

            if criteria.min_price is not None and item.price < criteria.min_price:
                filtered_out_count += 1
                continue
            if criteria.max_price is not None and item.price > criteria.max_price:
                filtered_out_count += 1
                continue

            if criteria.district:
                d_lower = criteria.district.lower()
                item_text = f"{item.district or ''} {item.street or ''} {item.title}".lower()
                if d_lower not in item_text:
                    filtered_out_count += 1
                    continue

            distance_km, is_within_radius = await _calc_geo_distance(db, f, item)

            duplicate = await find_duplicate(db, item.city, item.price, item.rooms, item.street)
            if duplicate:
                duplicate_count += 1
                continue

            try:
                details = await source.fetch_details(item.source_url)
            except Exception:
                logger.warning("Не вдалось завантажити деталі %s (%s)", item.source_url, source.name)
                continue

            description = details["description"]
            photos = details["photos"] or item.photos
            seller_type = details["seller_type"]

            if is_agency(item.title, description, seller_type):
                continue

            attrs = extract_attributes(item.title, description)
            if not passes_soft_filter(f, attrs):
                filtered_out_count += 1
                continue

            deviation = await calc_price_deviation(db, item.city, item.rooms, item.price)

            listing = Listing(
                source=source.name,
                source_url=item.source_url,
                title=item.title,
                description=description,
                price=item.price,
                region=item.region,
                city=item.city,
                district=item.district,
                street=item.street,
                latitude=item.latitude,
                longitude=item.longitude,
                distance_km=distance_km,
                is_within_radius=is_within_radius,
                rooms=attrs["rooms"] or item.rooms,
                area=details.get("area") or item.area,
                floor=details.get("floor") or item.floor,
                total_floors=details.get("total_floors") or item.total_floors,
                photos=photos,
                seller_type=seller_type,
                is_agency=False,
                price_vs_market_pct=deviation,
                property_type=attrs["property_type"],
                is_new_building=attrs["is_new_building"],
                furnished=attrs["furnished"],
                heating_type=attrs["heating_type"],
                has_elevator=attrs["has_elevator"],
                has_parking=attrs["has_parking"],
                has_balcony=attrs["has_balcony"],
                internet_included=attrs["internet_included"],
                utilities_included=attrs["utilities_included"],
                min_lease_months=attrs["min_lease_months"],
                deposit_required=attrs["deposit_required"],
            )
            db.add(listing)
            await db.flush()
            new_count += 1

            await asyncio.sleep(1)  # не бомбардуємо джерела запитами підряд


    return new_count, duplicate_count, filtered_out_count


def start_scheduler(interval_minutes: int):
    if not ACTIVE_SOURCES:
        logger.warning(
            "ENABLED_SOURCES не містить жодного відомого джерела — сканування нічого не знайде. "
            "Перевір значення змінної оточення (очікуються назви на кшталт 'olx,domria')."
        )

    scheduler.add_job(
        scan_all_filters,
        "interval",
        minutes=interval_minutes,
        id="scan_all",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info(
        "Планувальник запущено, інтервал перевірки — %s хв, увімкнені джерела: %s",
        interval_minutes, ", ".join(s.name for s in ACTIVE_SOURCES) or "жодного",
    )


async def run_filter_scan_now(filter_id: int):
    async with async_session() as db:
        f = await db.get(SearchFilter, filter_id)
        if f:
            try:
                await _scan_single_filter(db, f)
                f.last_scanned_at = datetime.utcnow()
                await db.commit()
            except Exception:
                logger.exception("Миттєвий скан фільтра #%s впав з помилкою", filter_id)


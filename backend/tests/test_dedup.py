import pytest
from services.dedup import find_duplicate
from models import Listing


async def _add_listing(db, city="Львів", price=10000, rooms=2, street="вул. Пекарська, 25", source_url=None):
    listing = Listing(
        source="olx",
        source_url=source_url or f"https://example.com/{id(object())}",
        title="Квартира",
        price=price,
        city=city,
        rooms=rooms,
        street=street,
    )
    db.add(listing)
    await db.commit()
    return listing


@pytest.mark.asyncio
class TestFindDuplicate:
    async def test_no_listings_no_duplicate(self, db_session):
        result = await find_duplicate(db_session, "Львів", 10000, 2, "вул. Пекарська, 25")
        assert result is None

    async def test_same_address_and_price_is_duplicate(self, db_session):
        await _add_listing(db_session, price=10000, street="вул. Пекарська, 25")
        result = await find_duplicate(db_session, "Львів", 10200, 2, "вул. Пекарська, 25")
        assert result is not None  # 2% різниці в межах толерантності 5%

    async def test_price_too_different_not_duplicate(self, db_session):
        await _add_listing(db_session, price=10000, street="вул. Пекарська, 25")
        result = await find_duplicate(db_session, "Львів", 13000, 2, "вул. Пекарська, 25")
        assert result is None  # 30% різниці — це вже інша квартира

    async def test_different_rooms_not_duplicate(self, db_session):
        await _add_listing(db_session, price=10000, rooms=1, street="вул. Пекарська, 25")
        result = await find_duplicate(db_session, "Львів", 10000, 3, "вул. Пекарська, 25")
        assert result is None

    async def test_different_city_not_duplicate(self, db_session):
        await _add_listing(db_session, city="Одеса", price=10000, street="вул. Пекарська, 25")
        result = await find_duplicate(db_session, "Львів", 10000, 2, "вул. Пекарська, 25")
        assert result is None

    async def test_no_street_never_matches(self, db_session):
        """Без адреси порівнювати тільки за ціною надто ризиковано (false positive) —
        функція свідомо відмовляється від дедупу в цьому випадку."""
        await _add_listing(db_session, price=10000, street="вул. Пекарська, 25")
        result = await find_duplicate(db_session, "Львів", 10000, 2, None)
        assert result is None

    async def test_similar_but_not_identical_address_matches(self, db_session):
        await _add_listing(db_session, price=10000, street="вулиця Пекарська 25")
        result = await find_duplicate(db_session, "Львів", 10000, 2, "вул. Пекарська, 25")
        assert result is not None

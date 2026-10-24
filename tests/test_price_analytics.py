import pytest
from services.price_analytics import calc_price_deviation
from models import Listing


async def _add_listing(db, city="Львів", rooms=2, price=10000, source_url=None):
    listing = Listing(
        source="olx",
        source_url=source_url or f"https://example.com/{price}-{rooms}-{id(object())}",
        title="Квартира",
        price=price,
        city=city,
        rooms=rooms,
    )
    db.add(listing)
    await db.commit()
    return listing


@pytest.mark.asyncio
class TestCalcPriceDeviation:
    async def test_no_data_returns_none(self, db_session):
        result = await calc_price_deviation(db_session, "Львів", 2, 10000)
        assert result is None

    async def test_price_above_average(self, db_session):
        await _add_listing(db_session, price=10000, source_url="https://a.com/1")
        await _add_listing(db_session, price=10000, source_url="https://a.com/2")

        result = await calc_price_deviation(db_session, "Львів", 2, 15000)
        assert result == 50.0  # на 50% вище середнього 10000

    async def test_price_below_average(self, db_session):
        await _add_listing(db_session, price=10000, source_url="https://a.com/3")

        result = await calc_price_deviation(db_session, "Львів", 2, 8000)
        assert result == -20.0

    async def test_filters_by_room_count(self, db_session):
        await _add_listing(db_session, rooms=1, price=6000, source_url="https://a.com/4")
        await _add_listing(db_session, rooms=3, price=20000, source_url="https://a.com/5")

        # 2-кімнатних оголошень немає — середнє по них не має рахуватись з 1- чи 3-кімнатних
        result = await calc_price_deviation(db_session, "Львів", 2, 10000)
        assert result is None

    async def test_filters_by_city(self, db_session):
        await _add_listing(db_session, city="Одеса", price=5000, source_url="https://a.com/6")

        result = await calc_price_deviation(db_session, "Львів", 2, 10000)
        assert result is None

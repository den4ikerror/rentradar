from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Listing


async def calc_price_deviation(db: AsyncSession, city: str, rooms: int | None, price: int) -> float | None:
    query = select(func.avg(Listing.price)).where(Listing.city == city)
    if rooms is not None:
        query = query.where(Listing.rooms == rooms)

    avg_price = (await db.execute(query)).scalar()
    if not avg_price:
        return None

    return round((price - float(avg_price)) / float(avg_price) * 100, 2)

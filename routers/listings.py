from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Listing, UserListingStatus, SearchFilter
from schemas import ListingOut, ListingStatusUpdate, ListingPage

router = APIRouter(prefix="/api/listings", tags=["listings"])

PAGE_SIZE = 20


@router.get("", response_model=ListingPage)
async def get_listings(
    city: str | None = None,
    exclude_hidden: bool = True,
    only_liked: bool = False,
    only_outside_radius: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    rows_status = (await db.execute(
        select(UserListingStatus.listing_id, UserListingStatus.status).where(
            UserListingStatus.user_id == 1
        )
    )).all()
    hidden_ids = [lid for lid, status in rows_status if status == "hidden"]
    liked_ids = [lid for lid, status in rows_status if status == "liked"]
    status_by_listing = {lid: status for lid, status in rows_status}

    query = select(Listing)

    # Застосовуємо активні фільтри користувача 1 (ціна, район, кімнати)
    active_filters = (await db.execute(
        select(SearchFilter).where(SearchFilter.user_id == 1, SearchFilter.is_active == True)
    )).scalars().all()

    if active_filters and not only_liked:
        cities = {f.city for f in active_filters if f.city}
        if city:
            query = query.where(Listing.city == city)
        elif cities:
            query = query.where(Listing.city.in_(cities))

        filter_clauses = []
        for f in active_filters:
            conds = []
            if f.min_price is not None:
                conds.append(Listing.price >= f.min_price)
            if f.max_price is not None:
                conds.append(Listing.price <= f.max_price)
            if f.district:
                d_lower = f.district.lower()
                conds.append(
                    func.lower(Listing.district).contains(d_lower) |
                    func.lower(Listing.street).contains(d_lower) |
                    func.lower(Listing.title).contains(d_lower) |
                    func.lower(Listing.description).contains(d_lower)
                )
            if f.room_options:
                conds.append(Listing.rooms.in_(f.room_options))

            if conds:
                filter_clauses.append(and_(*conds))

        if filter_clauses:
            query = query.where(or_(*filter_clauses))
    else:
        if city:
            query = query.where(Listing.city == city)

    if exclude_hidden and hidden_ids:
        query = query.where(Listing.id.notin_(hidden_ids))
    if only_liked:
        query = query.where(Listing.id.in_(liked_ids or [-1]))

    if only_outside_radius:
        query = query.where(Listing.is_within_radius == False)
    else:
        query = query.where(Listing.is_within_radius == True)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()

    query = query.order_by(Listing.created_at.desc()).offset(offset).limit(limit)
    rows = (await db.execute(query)).scalars().all()

    items = []
    for listing in rows:
        item = ListingOut.model_validate(listing)
        item.user_status = status_by_listing.get(listing.id)
        items.append(item)

    return ListingPage(items=items, total=total, offset=offset, limit=limit, has_more=offset + len(rows) < total)


@router.post("/{listing_id}/status")
async def set_status(
    listing_id: int,
    payload: ListingStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        select(UserListingStatus).where(
            UserListingStatus.user_id == 1,
            UserListingStatus.listing_id == listing_id,
        )
    )).scalar_one_or_none()

    if existing:
        existing.status = payload.status
    else:
        db.add(UserListingStatus(user_id=1, listing_id=listing_id, status=payload.status))

    await db.commit()
    return {"ok": True}


@router.delete("/{listing_id}/status")
async def clear_status(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        select(UserListingStatus).where(
            UserListingStatus.user_id == 1,
            UserListingStatus.listing_id == listing_id,
        )
    )).scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.commit()
    return {"ok": True}

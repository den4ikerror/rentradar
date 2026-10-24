import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import SearchFilter, Listing
from schemas import FilterCreate, FilterOut, SearchProgress
from scheduler import run_filter_scan_now


router = APIRouter(prefix="/api/filters", tags=["filters"])


@router.get("", response_model=list[FilterOut])
async def list_filters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SearchFilter))
    return result.scalars().all()


@router.post("", response_model=FilterOut)
async def create_filter(
    payload: FilterCreate,
    db: AsyncSession = Depends(get_db),
):
    f = SearchFilter(user_id=1, **payload.model_dump())
    db.add(f)
    await db.commit()
    await db.refresh(f)
    asyncio.create_task(run_filter_scan_now(f.id))
    return f


@router.patch("/{filter_id}", response_model=FilterOut)
async def update_filter(
    filter_id: int,
    payload: FilterCreate,
    db: AsyncSession = Depends(get_db),
):
    f = await db.get(SearchFilter, filter_id)
    if not f:
        raise HTTPException(404, "Фільтр не знайдено")
    for key, value in payload.model_dump().items():
        setattr(f, key, value)
    f.street_lat = None
    f.street_lon = None
    await db.commit()
    await db.refresh(f)
    return f


@router.patch("/{filter_id}/toggle", response_model=FilterOut)
async def toggle_filter(
    filter_id: int,
    db: AsyncSession = Depends(get_db),
):
    f = await db.get(SearchFilter, filter_id)
    if not f:
        raise HTTPException(404, "Фільтр не знайдено")
    f.is_active = not f.is_active
    await db.commit()
    await db.refresh(f)
    return f


@router.delete("/{filter_id}")
async def delete_filter(
    filter_id: int,
    db: AsyncSession = Depends(get_db),
):
    f = await db.get(SearchFilter, filter_id)
    if not f:
        raise HTTPException(404, "Фільтр не знайдено")
    await db.delete(f)
    await db.commit()
    return {"ok": True}


@router.get("/{filter_id}/progress", response_model=SearchProgress)
async def get_progress(
    filter_id: int,
    db: AsyncSession = Depends(get_db),
):
    f = await db.get(SearchFilter, filter_id)
    if not f:
        raise HTTPException(404, "Фільтр не знайдено")
    found_count = (await db.execute(
        select(func.count()).select_from(Listing).where(Listing.city == f.city)
    )).scalar_one()
    return SearchProgress(
        filter_id=f.id,
        is_scanning=f.last_scanned_at is None,
        last_scanned_at=f.last_scanned_at,
        found_count=found_count,
    )

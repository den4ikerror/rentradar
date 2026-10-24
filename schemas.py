from pydantic import BaseModel, Field
from datetime import datetime


class UserCreate(BaseModel):
    name: str


class UserOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserOut
    token: str


class FilterCreate(BaseModel):
    region: str | None = None
    city: str
    district: str | None = None
    street: str | None = None
    street_radius_km: float | None = Field(default=None, gt=0, le=50)

    min_price: int | None = None
    max_price: int | None = None
    room_options: list[int] = []
    min_area: float | None = None
    floor_not_first: bool = False
    floor_not_last: bool = False
    pets_allowed_only: bool = False

    property_types: list[str] = []
    renovation_type: str | None = None
    is_new_building: bool = False
    furnished_only: bool = False

    heating_type: str | None = None
    has_elevator: bool = False
    has_parking: bool = False
    has_balcony: bool = False
    internet_included: bool = False
    utilities_included: bool = False

    min_lease_months: int | None = None
    deposit_required: bool | None = None

    scan_interval_minutes: int = 60


class FilterOut(FilterCreate):
    id: int
    is_active: bool
    last_scanned_at: datetime | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ListingOut(BaseModel):
    id: int
    source: str
    source_url: str
    title: str
    price: int
    region: str | None
    city: str
    district: str | None
    street: str | None
    rooms: int | None
    area: float | None
    floor: int | None
    total_floors: int | None
    photos: list[str]
    property_type: str | None = None
    is_new_building: bool = False
    furnished: bool | None = None
    heating_type: str | None = None
    has_elevator: bool | None = None
    has_parking: bool | None = None
    has_balcony: bool | None = None
    internet_included: bool | None = None
    utilities_included: bool | None = None
    min_lease_months: int | None = None
    deposit_required: bool | None = None
    price_vs_market_pct: float | None
    distance_km: float | None = None
    is_within_radius: bool = True
    created_at: datetime
    user_status: str | None = None
    model_config = {"from_attributes": True}


class ListingStatusUpdate(BaseModel):
    status: str  # liked / hidden


class ListingPage(BaseModel):
    items: list[ListingOut]
    total: int
    offset: int
    limit: int
    has_more: bool


class SearchProgress(BaseModel):
    """Стан пошуку для екрана 'Шукаємо...' одразу після онбордингу."""
    filter_id: int
    is_scanning: bool
    last_scanned_at: datetime | None
    found_count: int

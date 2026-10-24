from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SearchCriteria:
    """Внутрішня уніфікована модель фільтра. Кожен адаптер сам вирішує,
    які поля він здатний передати в запит до свого сайту, а які застосувати
    вже після завантаження (post-filter)."""
    city: str
    region: str | None = None
    district: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    rooms: int | None = None
    min_area: float | None = None
    floor_not_first: bool = False
    floor_not_last: bool = False
    pets_allowed_only: bool = False
    property_types: list[str] = field(default_factory=list)
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


@dataclass
class ParsedListing:
    source: str
    source_url: str
    title: str
    price: int
    city: str
    region: str | None = None
    district: str | None = None
    street: str | None = None
    rooms: int | None = None
    area: float | None = None
    floor: int | None = None
    total_floors: int | None = None
    photos: list[str] = field(default_factory=list)
    description: str = ""
    seller_type: str = "unknown"  # private / company / unknown
    latitude: float | None = None
    longitude: float | None = None


class SourceAdapter(ABC):
    """Спільний контракт для всіх сайтів-джерел оголошень.
    Додати нове джерело = створити новий клас з такою ж сигнатурою
    і зареєструвати його в services/sources/__init__.py."""

    name: str

    @abstractmethod
    async def search(self, criteria: SearchCriteria, max_pages: int = 3) -> list[ParsedListing]:
        ...

    @abstractmethod
    async def fetch_details(self, url: str) -> dict:
        """Повертає {'description': str, 'photos': list[str], 'seller_type': str,
        'area': float|None, 'floor': int|None, 'total_floors': int|None}"""
        ...

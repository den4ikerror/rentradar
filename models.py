from sqlalchemy import String, Integer, BigInteger, Boolean, ForeignKey, Numeric, Text, JSON, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    filters: Mapped[list["SearchFilter"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class SearchFilter(Base):
    __tablename__ = "search_filters"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # Географія — заповнюється настільки детально, наскільки обрав користувач.
    # Кожен парсер джерела сам вирішує, які з цих полів він здатний використати.
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)     # область
    city: Mapped[str] = mapped_column(String(100))                            # місто (обов'язкове)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)  # район міста
    street: Mapped[str | None] = mapped_column(String(200), nullable=True)    # вулиця-орієнтир (для студентів і т.п.)
    street_radius_km: Mapped[float | None] = mapped_column(Float, nullable=True)  # макс. відстань від вулиці
    street_lat: Mapped[float | None] = mapped_column(Float, nullable=True)    # геокодовано один раз при створенні фільтра
    street_lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    min_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    room_options: Mapped[list] = mapped_column(JSON, default=list)  # [1,2,4] — можна кілька значень одночасно
    min_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    floor_not_first: Mapped[bool] = mapped_column(Boolean, default=False)
    floor_not_last: Mapped[bool] = mapped_column(Boolean, default=False)
    pets_allowed_only: Mapped[bool] = mapped_column(Boolean, default=False)

    # Тип житла й стан
    property_types: Mapped[list] = mapped_column(JSON, default=list)  # ['apartment','studio',...] — можна кілька
    renovation_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # euro/cosmetic/needs_repair/designer
    is_new_building: Mapped[bool] = mapped_column(Boolean, default=False)
    furnished_only: Mapped[bool] = mapped_column(Boolean, default=False)

    # Комунікації та зручності
    heating_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # central/autonomous/electric
    has_elevator: Mapped[bool] = mapped_column(Boolean, default=False)
    has_parking: Mapped[bool] = mapped_column(Boolean, default=False)
    has_balcony: Mapped[bool] = mapped_column(Boolean, default=False)
    internet_included: Mapped[bool] = mapped_column(Boolean, default=False)
    utilities_included: Mapped[bool] = mapped_column(Boolean, default=False)

    # Умови оренди
    min_lease_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deposit_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # None = байдуже

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    scan_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="filters")


class Listing(Base):
    __tablename__ = "listings"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_url: Mapped[str] = mapped_column(String(500), unique=True)
    source: Mapped[str] = mapped_column(String(30))  # olx / domria / lunua / rieltor / flatfy
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer)

    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    street: Mapped[str | None] = mapped_column(String(200), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_within_radius: Mapped[bool] = mapped_column(Boolean, default=True)

    rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area: Mapped[float | None] = mapped_column(Float, nullable=True)
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[int | None] = mapped_column(Integer, nullable=True)

    photos: Mapped[list] = mapped_column(JSON, default=list)
    seller_type: Mapped[str] = mapped_column(String(20), default="unknown")  # private / company / unknown
    is_agency: Mapped[bool] = mapped_column(Boolean, default=False)


    # Атрибути, видобуті евристичним аналізом тексту оголошення (services/attribute_extraction.py).
    # None означає "текст не дає однозначного сигналу" — це навмисно, щоб фільтр за замовчуванням
    # не відкидав оголошення через відсутність згадки, а не через реальну невідповідність.
    property_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_new_building: Mapped[bool] = mapped_column(Boolean, default=False)
    furnished: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    heating_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    has_elevator: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_parking: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_balcony: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    internet_included: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    utilities_included: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    min_lease_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deposit_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    price_vs_market_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserListingStatus(Base):
    __tablename__ = "user_listing_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20))  # liked / hidden
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class GeocodeCache(Base):
    """Кеш геокодування (адреса -> координати), щоб не бити по Nominatim
    частіше ніж дозволяє ліміт 1 запит/сек і не сповільнювати повторні скани."""
    __tablename__ = "geocode_cache"
    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RegistrationLog(Base):
    """Лог реєстрацій за IP — без нього анонімна реєстрація (лише ім'я, без email/пароля)
    дозволяє будь-кому наплодити необмежену кількість акаунтів і обійти MAX_FILTERS_PER_USER,
    вичерпавши спільний безкоштовний ліміт Gemini API на всіх користувачів разом."""
    __tablename__ = "registration_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    ip_address: Mapped[str] = mapped_column(String(45), index=True)  # вистачає під IPv6
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

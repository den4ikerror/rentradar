import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./rentfinder.db")
    SCAN_INTERVAL_MINUTES: int = int(os.getenv("SCAN_INTERVAL_MINUTES", "15"))
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    NOMINATIM_CONTACT_EMAIL: str = os.getenv("NOMINATIM_CONTACT_EMAIL", "you@example.com")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = int(os.getenv("JWT_EXPIRE_DAYS", "30"))

    # Джерела, ввімкнені для сканування. За замовчуванням — усі 5 джерел:
    ENABLED_SOURCES: list[str] = os.getenv("ENABLED_SOURCES", "olx,domria,lunua,rieltor,flatfy").split(",")

    MAX_FILTERS_PER_USER: int = int(os.getenv("MAX_FILTERS_PER_USER", "5"))
    MAX_REGISTRATIONS_PER_IP_PER_DAY: int = int(os.getenv("MAX_REGISTRATIONS_PER_IP_PER_DAY", "3"))


settings = Settings()

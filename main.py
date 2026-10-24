import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from config import settings
from database import init_db, async_session
from scheduler import start_scheduler, ACTIVE_SOURCES
from services.logger_store import setup_memory_logging
from routers import auth, filters, listings, reference


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
setup_memory_logging()
logger = logging.getLogger("rentfinder")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    if not settings.JWT_SECRET:
        logger.error(
            "JWT_SECRET не задано — вхід користувачів працюватиме некоректно (буде HTTP 500 при спробі "
            "видати токен). Згенеруй випадковий секрет (openssl rand -hex 32) і додай у .env перед стартом."
        )

    start_scheduler(settings.SCAN_INTERVAL_MINUTES)

    logger.info("RentFinder backend запущено")
    yield



app = FastAPI(title="RentFinder", lifespan=lifespan)

_cors_wildcard = settings.CORS_ORIGINS == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=not _cors_wildcard,  # браузери відхиляють Access-Control-Allow-Credentials разом з "*"
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Будь-яка неочікувана помилка повертає зрозумілу відповідь замість голого 500,
    # щоб фронтенд міг показати користувачу коректне повідомлення, а не "зависнути".
    logger.exception("Необроблена помилка на %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Щось пішло не так на сервері. Спробуйте ще раз за хвилину."},
    )


app.include_router(auth.router)
app.include_router(filters.router)
app.include_router(listings.router)
app.include_router(reference.router)


@app.get("/health")
async def health():
    try:
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unavailable"

    return {
        "status": "ok",
        "database": db_status,
        "auth_configured": bool(settings.JWT_SECRET),
        "active_sources": [s.name for s in ACTIVE_SOURCES],
    }


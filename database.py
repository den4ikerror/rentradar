from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"timeout": 30},
)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for col_def in [
            "ALTER TABLE listings ADD COLUMN distance_km FLOAT",
            "ALTER TABLE listings ADD COLUMN is_within_radius BOOLEAN DEFAULT 1",
            "ALTER TABLE listings ADD COLUMN price_vs_market_pct FLOAT",
        ]:
            try:
                await conn.execute(text(col_def))
            except Exception:
                pass

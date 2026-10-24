import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database import Base
import models  # noqa: F401 — реєструє всі моделі в metadata перед create_all


@pytest_asyncio.fixture
async def db_session():
    """Свіжа in-memory SQLite база на кожен тест — швидко, ізольовано, без побічних
    ефектів між тестами (на відміну від спільної тестової БД на диску)."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()

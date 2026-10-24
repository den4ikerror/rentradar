import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import User


def create_access_token(user_id: int) -> str:
    if not settings.JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET не задано в .env. Це критично: без нього неможливо безпечно "
            "підписувати токени входу. Згенеруй випадковий рядок (напр. `openssl rand -hex 32`) "
            "і додай як JWT_SECRET у backend/.env перед запуском."
        )
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Сесія закінчилась, увійди ще раз")
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(401, "Недійсний токен авторизації")


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Кожен захищений ендпоінт бере користувача звідси, а не з параметра шляху —
    інакше будь-хто, підставивши чужий числовий user_id в URL, міг би читати
    чи змінювати не свої дані (IDOR). Токен видається одноразово при вході
    через Telegram Login Widget і передається як 'Authorization: Bearer <token>'."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Потрібна авторизація")

    user_id = _decode_token(authorization.removeprefix("Bearer ").strip())
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(401, "Користувача не знайдено")
    return user

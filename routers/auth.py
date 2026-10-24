import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import User, RegistrationLog
from schemas import UserCreate, UserOut, AuthResponse
from services.auth import create_access_token, get_current_user
from services.request_ip import get_client_ip

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register", response_model=AuthResponse)
async def register(payload: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """Проста анонімна реєстрація за іменем — без Telegram, email чи пароля.
    Єдиний бар'єр проти зловживання (масове створення акаунтів заради обходу
    MAX_FILTERS_PER_USER і накрутки AI-викликів на спільному Gemini-ключі) —
    ліміт кількості реєстрацій з однієї IP-адреси за добу."""
    ip = get_client_ip(request)
    since = datetime.utcnow() - timedelta(days=1)
    recent_count = (await db.execute(
        select(func.count()).select_from(RegistrationLog).where(
            RegistrationLog.ip_address == ip,
            RegistrationLog.created_at >= since,
        )
    )).scalar_one()

    if recent_count >= settings.MAX_REGISTRATIONS_PER_IP_PER_DAY:
        raise HTTPException(
            429,
            f"Забагато нових акаунтів з цієї адреси за останню добу "
            f"(ліміт {settings.MAX_REGISTRATIONS_PER_IP_PER_DAY}). Спробуй пізніше.",
        )

    for _ in range(5):
        candidate_id = secrets.randbits(48)
        db.add(User(telegram_id=candidate_id, name=payload.name))
        try:
            await db.commit()
            break
        except IntegrityError:
            await db.rollback()
    else:
        raise RuntimeError("Не вдалось згенерувати унікальний ідентифікатор користувача")

    user = (await db.execute(
        select(User).where(User.telegram_id == candidate_id)
    )).scalar_one()

    db.add(RegistrationLog(ip_address=ip))
    await db.commit()

    token = create_access_token(user.id)
    return AuthResponse(user=UserOut.model_validate(user), token=token)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

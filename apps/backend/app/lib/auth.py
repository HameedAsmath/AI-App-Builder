import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.config import get_settings
from app.lib.db import get_session
from app.models import User

COOKIE_NAME = "access_token"
ALGORITHM = "HS256"
_hasher = PasswordHasher()


# --- Passwords ---
def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


# --- JWT ---
def create_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),  # "subject" = who this token is for
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def read_token(token: str) -> uuid.UUID | None:
    """Returns the user id, or None if the token is fake, tampered with or expired."""
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
        return uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None


# --- Use in any route: user = Depends(get_current_user) ---
async def get_current_user(
    token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: AsyncSession = Depends(get_session),
) -> User:
    user_id = read_token(token) if token else None
    user = await db.get(User, user_id) if user_id else None
    if not user:
        raise HTTPException(401, "Not logged in")
    return user
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.auth import COOKIE_NAME, create_token, get_current_user, hash_password, verify_password
from app.lib.config import get_settings
from app.lib.db import get_session
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str


def set_auth_cookie(response: Response, user: User) -> None:
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        create_token(user.id),
        httponly=True,   # JS can't read it → safe from XSS
        samesite="lax",  # CSRF protection
        secure=settings.environment == "production",
        max_age=settings.jwt_expire_days * 24 * 60 * 60,
    )


@router.post("/signup", status_code=201)
async def signup(body: SignupBody, response: Response, db: AsyncSession = Depends(get_session)) -> UserOut:
    user = User(email=body.email.lower(), password_hash=hash_password(body.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        raise HTTPException(409, "Email already registered")
    set_auth_cookie(response, user)
    return UserOut(id=user.id, email=user.email)


@router.post("/login")
async def login(body: LoginBody, response: Response, db: AsyncSession = Depends(get_session)) -> UserOut:
    user = await db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    set_auth_cookie(response, user)
    return UserOut(id=user.id, email=user.email)


@router.post("/logout", status_code=204)
async def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME)  # nothing stored on the server to delete


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email)
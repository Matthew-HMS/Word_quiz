from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def validate_bcrypt_password(password: str) -> None:
    """bcrypt only uses the first 72 bytes of a password.

    passlib raises ValueError for longer inputs; validate up-front so we can
    return a user-friendly 400 instead of a 500.
    """
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes (bcrypt limit)")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    now = dt.datetime.now(dt.UTC)
    exp = now + dt.timedelta(minutes=settings.access_token_exp_minutes)
    payload: dict[str, Any] = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise cred_exc
    except JWTError:
        raise cred_exc

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise cred_exc

    q = select(User).where(User.id == user_id)
    user = db.execute(q).scalar_one_or_none()
    if user is None:
        raise cred_exc
    return user

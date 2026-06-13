from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.models import User


# tokenUrl is informational only (used by the OpenAPI docs "Authorize" button);
# clients obtain the bearer token from /api/auth/google.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/google")

# Reused across requests; caches Google's signing certificates.
_google_request = google_requests.Request()


def create_access_token(subject: str) -> str:
    now = dt.datetime.now(dt.UTC)
    exp = now + dt.timedelta(minutes=settings.access_token_exp_minutes)
    payload: dict[str, Any] = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_google_token(credential: str) -> dict[str, Any]:
    """Verify a Google ID token (the `credential` from Google Identity Services).

    Returns the decoded claims (sub, email, name, picture, ...) on success.
    Raises HTTP 401 if the token is invalid or not issued for our client.
    """
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google sign-in is not configured (GOOGLE_CLIENT_ID is unset)",
        )
    try:
        claims = google_id_token.verify_oauth2_token(
            credential, _google_request, settings.google_client_id
        )
    except Exception as e:  # verify_oauth2_token raises ValueError / GoogleAuthError
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential",
        ) from e

    if not claims.get("email_verified", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google email not verified")
    return claims


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

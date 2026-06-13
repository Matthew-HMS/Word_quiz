from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, verify_google_token
from app.db import get_db
from app.models import User
from app.schemas import GoogleAuthRequest, TokenResponse, UserMeResponse


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
def google_login(req: GoogleAuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    claims = verify_google_token(req.credential)

    sub = str(claims["sub"])
    email = str(claims["email"])
    name = claims.get("name")
    picture = claims.get("picture")

    # Find by Google subject first, then fall back to email so legacy/email
    # accounts get linked to their Google identity on first sign-in.
    user = db.execute(select(User).where(User.google_sub == sub)).scalar_one_or_none()
    if user is None:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    if user is None:
        user = User(email=email, google_sub=sub, name=name, picture=picture)
        db.add(user)
    else:
        # Keep identity fields current.
        user.google_sub = sub
        user.email = email
        if name:
            user.name = name
        if picture:
            user.picture = picture

    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserMeResponse)
def me(user: User = Depends(get_current_user)) -> UserMeResponse:
    return UserMeResponse(id=user.id, email=user.email, name=user.name, picture=user.picture)

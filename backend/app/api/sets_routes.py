from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import CreateSetRequest, SetListItem
from app.services.sets_service import (
    SetExistsError,
    SetNotFoundError,
    add_word,
    create_set,
    delete_set,
    delete_word,
    import_csv,
    list_sets,
    load_set,
)


class VocabRequest(BaseModel):
    word: str
    translation: str


router = APIRouter(prefix="/api/sets", tags=["sets"])


@router.get("", response_model=list[SetListItem])
def get_sets(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[SetListItem]:
    return [SetListItem(name=name, word_count=count) for name, count in list_sets(db, user)]


@router.post("", status_code=201)
def create_new_set(
    req: CreateSetRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        vset = create_set(db, user, req.name)
    except SetExistsError:
        raise HTTPException(status_code=400, detail="A set with that name already exists")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "Set created", "name": vset.name}


@router.post("/import", status_code=201)
async def import_set(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    # Derive set name from form field, else the uploaded filename (sans .csv).
    set_name = (name or "").strip()
    if not set_name:
        fn = (file.filename or "").strip()
        set_name = fn[:-4] if fn.lower().endswith(".csv") else fn
    if not set_name:
        raise HTTPException(status_code=400, detail="A set name is required")

    try:
        vset = import_csv(db, user, set_name, raw)
    except SetExistsError:
        raise HTTPException(status_code=400, detail="A set with that name already exists")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "Set imported", "name": vset.name, "word_count": len(vset.words)}


@router.delete("/{set_name}")
def delete_existing_set(
    set_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not delete_set(db, user, set_name):
        raise HTTPException(status_code=404, detail="Set not found")
    return {"detail": "Set deleted"}


@router.get("/{set_name}/vocab")
def get_set_vocab(set_name: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        data = load_set(db, user, set_name)
    except SetNotFoundError:
        raise HTTPException(status_code=404, detail="Set not found")
    except ValueError:
        # Empty set is valid for editing; return an empty list.
        return []
    return [{"word": k, "translation": v} for k, v in data.items()]


@router.post("/{set_name}/vocab")
def add_set_vocab(
    set_name: str,
    req: VocabRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        added = add_word(db, user, set_name, req.word, req.translation)
    except SetNotFoundError:
        raise HTTPException(status_code=404, detail="Set not found")
    if not added:
        raise HTTPException(status_code=400, detail="Word already exists")
    return {"detail": "Word added"}


@router.delete("/{set_name}/vocab/{word}")
def delete_set_vocab(
    set_name: str,
    word: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        deleted = delete_word(db, user, set_name, word)
    except SetNotFoundError:
        raise HTTPException(status_code=404, detail="Set not found")
    if not deleted:
        raise HTTPException(status_code=404, detail="Word not found")
    return {"detail": "Word deleted"}

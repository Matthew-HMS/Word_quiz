from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.models import User
from app.schemas import SetListItem
from app.services.sets_service import list_sets, load_set, add_word, delete_word


class VocabRequest(BaseModel):
    word: str
    translation: str

router = APIRouter(prefix="/api/sets", tags=["sets"])


@router.get("", response_model=list[SetListItem])
def get_sets(_: User = Depends(get_current_user)) -> list[SetListItem]:
    return [SetListItem(name=name, size_bytes=size) for name, size in list_sets()]

@router.get("/{set_name}/vocab")
def get_set_vocab(set_name: str, _: User = Depends(get_current_user)):
    try:
        data = load_set(set_name)
        return [{"word": k, "translation": v} for k, v in data.items()]
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{set_name}/vocab")
def add_set_vocab(set_name: str, req: VocabRequest, _: User = Depends(get_current_user)):
    try:
        added = add_word(set_name, req.word, req.translation)
        if not added:
            raise HTTPException(status_code=400, detail="Word already exists")
        return {"detail": "Word added"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Set not found")

@router.delete("/{set_name}/vocab/{word}")
def delete_set_vocab(set_name: str, word: str, _: User = Depends(get_current_user)):
    try:
        deleted = delete_word(set_name, word)
        if not deleted:
            raise HTTPException(status_code=404, detail="Word not found")
        return {"detail": "Word deleted"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Set not found")


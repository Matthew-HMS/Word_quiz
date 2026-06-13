from __future__ import annotations

import csv
import io

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User, VocabSet, VocabWord


class SetNotFoundError(Exception):
    """Raised when a set name does not exist for the given user."""


class SetExistsError(Exception):
    """Raised when creating a set whose name is already taken by the user."""


def _get_set(db: Session, user: User, set_name: str) -> VocabSet | None:
    return db.execute(
        select(VocabSet).where(VocabSet.user_id == user.id, VocabSet.name == set_name)
    ).scalar_one_or_none()


def list_sets(db: Session, user: User) -> list[tuple[str, int]]:
    """Return (name, word_count) for each of the user's sets, sorted by name."""
    rows = db.execute(
        select(VocabSet.name, func.count(VocabWord.id))
        .outerjoin(VocabWord, VocabWord.set_id == VocabSet.id)
        .where(VocabSet.user_id == user.id)
        .group_by(VocabSet.id, VocabSet.name)
    ).all()
    return sorted(((name, int(count)) for name, count in rows), key=lambda x: x[0].lower())


def load_set(db: Session, user: User, set_name: str) -> dict[str, str]:
    """Return the set's words as an ordered {word: translation} dict.

    Raises SetNotFoundError if the set does not exist, ValueError if empty.
    """
    vset = _get_set(db, user, set_name)
    if vset is None:
        raise SetNotFoundError(set_name)
    study_set: dict[str, str] = {w.word: w.translation for w in vset.words}
    if not study_set:
        raise ValueError("Empty set")
    return study_set


def create_set(db: Session, user: User, set_name: str) -> VocabSet:
    name = set_name.strip()
    if not name:
        raise ValueError("Set name cannot be empty")
    if _get_set(db, user, name) is not None:
        raise SetExistsError(name)
    vset = VocabSet(user_id=user.id, name=name)
    db.add(vset)
    db.commit()
    db.refresh(vset)
    return vset


def delete_set(db: Session, user: User, set_name: str) -> bool:
    vset = _get_set(db, user, set_name)
    if vset is None:
        return False
    db.delete(vset)
    db.commit()
    return True


def add_word(db: Session, user: User, set_name: str, word: str, translation: str) -> bool:
    """Add a word to the set. Returns False if the word already exists."""
    vset = _get_set(db, user, set_name)
    if vset is None:
        raise SetNotFoundError(set_name)
    exists = db.execute(
        select(VocabWord).where(VocabWord.set_id == vset.id, VocabWord.word == word)
    ).scalar_one_or_none()
    if exists is not None:
        return False
    next_pos = db.execute(
        select(func.coalesce(func.max(VocabWord.position), -1)).where(VocabWord.set_id == vset.id)
    ).scalar_one() + 1
    db.add(VocabWord(set_id=vset.id, word=word, translation=translation, position=next_pos))
    db.commit()
    return True


def delete_word(db: Session, user: User, set_name: str, word: str) -> bool:
    vset = _get_set(db, user, set_name)
    if vset is None:
        raise SetNotFoundError(set_name)
    target = db.execute(
        select(VocabWord).where(VocabWord.set_id == vset.id, VocabWord.word == word)
    ).scalar_one_or_none()
    if target is None:
        return False
    db.delete(target)
    db.commit()
    return True


def import_csv(db: Session, user: User, set_name: str, raw: bytes) -> VocabSet:
    """Create a new set from CSV bytes. Each row is `word,translation`.

    Raises SetExistsError if the name is taken, ValueError if no valid rows.
    """
    name = set_name.strip()
    if not name:
        raise ValueError("Set name cannot be empty")
    if _get_set(db, user, name) is not None:
        raise SetExistsError(name)

    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))

    words: list[VocabWord] = []
    seen: set[str] = set()
    vset = VocabSet(user_id=user.id, name=name)
    for row in reader:
        if len(row) < 2:
            continue
        w = row[0].strip()
        t = row[1].strip()
        if not w or not t or w in seen:
            continue
        seen.add(w)
        words.append(VocabWord(word=w, translation=t, position=len(words)))

    if not words:
        raise ValueError("CSV contained no valid 'word,translation' rows")

    vset.words = words
    db.add(vset)
    db.commit()
    db.refresh(vset)
    return vset

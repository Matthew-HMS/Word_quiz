from __future__ import annotations

import csv
from pathlib import Path

from app.core.config import settings


def list_sets() -> list[tuple[str, int]]:
    sets_dir = settings.resolved_sets_dir()
    if not sets_dir.exists():
        return []
    rows: list[tuple[str, int]] = []
    for p in sets_dir.iterdir():
        if p.is_file() and p.suffix.lower() == ".csv":
            rows.append((p.name, p.stat().st_size))
    return sorted(rows, key=lambda x: x[0].lower())


def load_set(set_name: str) -> dict[str, str]:
    sets_dir = settings.resolved_sets_dir()
    target = (sets_dir / set_name).resolve()
    if sets_dir.resolve() not in target.parents:
        raise ValueError("Invalid set name")
    if not target.exists() or target.suffix.lower() != ".csv":
        raise FileNotFoundError(set_name)

    study_set: dict[str, str] = {}
    with target.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            study_set[row[0]] = row[1]
    if not study_set:
        raise ValueError("Empty set")
    return study_set

def add_word(set_name: str, word: str, translation: str) -> bool:
    try:
        study_set = load_set(set_name)
    except Exception:
        study_set = {}
    if word in study_set:
        return False
    sets_dir = settings.resolved_sets_dir()
    target = (sets_dir / set_name).resolve()
    if sets_dir.resolve() not in target.parents:
        return False
        
    try:
        with target.open("rb+") as fb:
            fb.seek(0, 2)
            if fb.tell() > 0:
                fb.seek(-1, 2)
                if fb.read(1) != b"\n":
                    fb.write(b"\n")
    except OSError:
        pass
        
    with target.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([word, translation])
    return True

def delete_word(set_name: str, word: str) -> bool:
    try:
        study_set = load_set(set_name)
    except Exception:
        return False
    if word not in study_set:
        return False
    sets_dir = settings.resolved_sets_dir()
    target = (sets_dir / set_name).resolve()
    rows = []
    with target.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row: continue
            if row[0] == word: continue
            rows.append(row)
    with target.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return True

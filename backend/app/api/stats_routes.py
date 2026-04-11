from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import QuizHistory, User


router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def stats(set: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(QuizHistory).where(QuizHistory.user_id == user.id)
    if set:
        q = q.where(QuizHistory.set_name == set)

    rows = db.execute(q.order_by(QuizHistory.ts.asc())).scalars().all()
    if not rows:
        return {"total_sessions": 0, "average_accuracy": 0.0, "top_wrong": []}

    avg = sum(r.accuracy for r in rows) / len(rows)

    # aggregate wrong words
    wrong_counts: dict[str, int] = {}
    wrong_ch: dict[str, str] = {}
    for r in rows:
        for ww in r.wrong_words or []:
            en = ww.get("en") if isinstance(ww, dict) else None
            if not isinstance(en, str) or not en:
                continue
            cnt = ww.get("count") if isinstance(ww, dict) else 1
            try:
                cnt_int = int(cnt) if cnt is not None else 1
            except (TypeError, ValueError):
                cnt_int = 1
            wrong_counts[en] = wrong_counts.get(en, 0) + max(cnt_int, 1)
            ch = ww.get("ch") if isinstance(ww, dict) else None
            if isinstance(ch, str) and ch and en not in wrong_ch:
                wrong_ch[en] = ch

    top10 = sorted(wrong_counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:10]

    return {
        "total_sessions": len(rows),
        "average_accuracy": round(avg, 2),
        "last_session": {
            "ts": rows[-1].ts,
            "set": rows[-1].set_name,
            "mode": rows[-1].mode,
            "accuracy": rows[-1].accuracy,
        },
        "top_wrong": [
            {"en": en, "count": cnt, "ch": wrong_ch.get(en, "")} for en, cnt in top10
        ],
    }

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import QuizHistory, QuizSession, User
from app.schemas import (
    AnswerRequest,
    AnswerResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    QuestionResponse,
    ResultResponse,
)
from app.services.quiz_engine import build_question, finalize_result, init_state, submit_answer
from app.services.sets_service import load_set


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=CreateSessionResponse)
def create_session(
    req: CreateSessionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreateSessionResponse:
    try:
        study_set = load_set(req.set)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Set not found")

    if req.mode in ("en-to-ch", "ch-to-en") and len(study_set) < 4:
        raise HTTPException(status_code=400, detail="Multiple-choice modes require at least 4 words")

    keys = list(study_set.keys())

    # weak_only MVP: based on user's historical wrong words in DB for this set
    if req.weak_only:
        rows = db.execute(
            select(QuizHistory).where(QuizHistory.user_id == user.id, QuizHistory.set_name == req.set)
        ).scalars().all()
        weak: set[str] = set()
        for r in rows:
            for ww in r.wrong_words or []:
                en = ww.get("en") if isinstance(ww, dict) else None
                if isinstance(en, str) and en:
                    weak.add(en)
        keys = [k for k in keys if k in weak]
        if not keys:
            raise HTTPException(status_code=400, detail="No weak words found for this set yet")

    state = init_state(req.mode, study_set, keys)

    session = QuizSession(user_id=user.id, set_name=req.set, mode=req.mode, state=state)
    db.add(session)
    db.commit()
    db.refresh(session)

    return CreateSessionResponse(session_id=session.id)


@router.get("/{session_id}/question", response_model=QuestionResponse)
def get_question(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuestionResponse:
    session = db.execute(
        select(QuizSession).where(QuizSession.id == session_id, QuizSession.user_id == user.id)
    ).scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    study_set = load_set(session.set_name)

    def _progress_str(state: dict) -> str:
        progress = int(state.get("idx", 0) or 0)
        total = len(state.get("keys") or [])
        return f"({min(progress + 1, max(total, 1))}/{max(total, 1)})"

    # If pending spell retry, return that prompt
    pending = session.state.get("pending") if isinstance(session.state, dict) else None
    if isinstance(pending, dict) and pending.get("kind") == "spell_retry":
        word = pending.get("word")
        return QuestionResponse(
            session_id=session.id,
            kind="spelling",
            prompt=f"\"{word}\"",
            choices=None,
            progress=_progress_str(session.state),
            tts_text=str(word) if isinstance(word, str) else None,
        )

    # Build question and persist it so the subsequent /answer validates against the same question
    q = build_question(session.state, study_set)

    # Mirror CLI behavior: if a word can't be asked due to insufficient choices, skip it immediately.
    while q.get("kind") == "skip":
        session.state["idx"] = int(session.state.get("idx", 0) or 0) + 1
        session.state["current"] = None
        q = build_question(session.state, study_set)

    # Persist any state changes caused by build_question / skipping
    flag_modified(session, "state")
    db.add(session)
    db.commit()
    db.refresh(session)

    if q.get("kind") == "finished":
        return QuestionResponse(
            session_id=session.id,
            kind="spelling",
            prompt="Finished",
            choices=None,
            progress=_progress_str(session.state),
            tts_text=None,
        )

    progress_str = _progress_str(session.state)

    if q["kind"] == "spelling":
        return QuestionResponse(
            session_id=session.id,
            kind="spelling",
            prompt=q["prompt"],
            choices=None,
            progress=progress_str,
            tts_text=str(q.get("answer")) if isinstance(q.get("answer"), str) else None,
        )

    return QuestionResponse(
        session_id=session.id,
        kind="multiple_choice",
        prompt=q["prompt"],
        choices=q["choices"],
        progress=progress_str,
        tts_text=str(q.get("word")) if isinstance(q.get("word"), str) else None,
    )


@router.post("/{session_id}/answer", response_model=AnswerResponse)
def answer(
    session_id: uuid.UUID,
    req: AnswerRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnswerResponse:
    session = db.execute(
        select(QuizSession).where(QuizSession.id == session_id, QuizSession.user_id == user.id)
    ).scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    study_set = load_set(session.set_name)

    res = submit_answer(session.state, study_set, choice=req.choice, text=req.text)
    # persist state
    flag_modified(session, "state")
    db.add(session)
    db.commit()
    db.refresh(session)

    next_kind = res["next"]

    if next_kind == "finished":
        engine_result = finalize_result(session.state)
        history = QuizHistory(
            user_id=user.id,
            set_name=session.set_name,
            mode=session.mode,
            correct=engine_result.correct,
            wrong=engine_result.wrong,
            accuracy=engine_result.accuracy,
            wrong_words=engine_result.wrong_words_first_attempt,
        )
        db.add(history)
        db.commit()

    return AnswerResponse(
        correct=bool(res["correct"]),
        feedback=str(res["feedback"]),
        next_kind=next_kind if next_kind in ("question", "spell_retry", "finished") else "question",
    )


@router.get("/{session_id}/result", response_model=ResultResponse)
def result(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResultResponse:
    session = db.execute(
        select(QuizSession).where(QuizSession.id == session_id, QuizSession.user_id == user.id)
    ).scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    engine_result = finalize_result(session.state)
    return ResultResponse(
        correct=engine_result.correct,
        wrong=engine_result.wrong,
        accuracy=engine_result.accuracy,
        wrong_words_first_attempt=engine_result.wrong_words_first_attempt,
    )

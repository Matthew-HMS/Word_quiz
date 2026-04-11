from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


QuizMode = Literal["en-to-ch", "ch-to-en", "en-spelling"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class UserMeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr


class SetListItem(BaseModel):
    name: str
    size_bytes: int


class CreateSessionRequest(BaseModel):
    set: str
    mode: QuizMode
    weak_only: bool = False


class CreateSessionResponse(BaseModel):
    session_id: uuid.UUID


class QuestionResponse(BaseModel):
    session_id: uuid.UUID
    kind: Literal["multiple_choice", "spelling"]
    prompt: str
    choices: list[str] | None = None
    progress: str
    # Text that the UI should send to /api/tts (matches main.py which speaks the English word)
    tts_text: str | None = None


class AnswerRequest(BaseModel):
    # multiple_choice: choose 1-4
    choice: int | None = Field(default=None, ge=1, le=4)
    # spelling: typed answer
    text: str | None = None


class AnswerResponse(BaseModel):
    correct: bool
    feedback: str
    next_kind: Literal["question", "spell_retry", "finished"]


class ResultResponse(BaseModel):
    correct: int
    wrong: int
    accuracy: float
    wrong_words_first_attempt: list[dict]

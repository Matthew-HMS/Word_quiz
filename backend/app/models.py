from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)

    # Google SSO is the only auth method. password_hash is kept (nullable) for
    # backward compatibility with any legacy rows but is no longer written.
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    sessions: Mapped[list[QuizSession]] = relationship(back_populates="user")  # type: ignore[name-defined]
    vocab_sets: Mapped[list[VocabSet]] = relationship(  # type: ignore[name-defined]
        back_populates="user", cascade="all, delete-orphan"
    )


class VocabSet(Base):
    __tablename__ = "vocab_sets"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_vocab_sets_user_name"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped[User] = relationship(back_populates="vocab_sets")
    words: Mapped[list[VocabWord]] = relationship(  # type: ignore[name-defined]
        back_populates="vocab_set",
        cascade="all, delete-orphan",
        order_by="VocabWord.position",
    )


class VocabWord(Base):
    __tablename__ = "vocab_words"
    __table_args__ = (UniqueConstraint("set_id", "word", name="uq_vocab_words_set_word"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    set_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("vocab_sets.id", ondelete="CASCADE"), index=True
    )
    word: Mapped[str] = mapped_column(Text)
    translation: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)

    vocab_set: Mapped[VocabSet] = relationship(back_populates="words")


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), index=True)

    set_name: Mapped[str] = mapped_column(String(255), index=True)
    mode: Mapped[str] = mapped_column(String(32), index=True)
    state: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped[User] = relationship(back_populates="sessions")


class QuizHistory(Base):
    __tablename__ = "quiz_history"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), index=True)

    ts: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    set_name: Mapped[str] = mapped_column(String(255), index=True)
    mode: Mapped[str] = mapped_column(String(32), index=True)

    correct: Mapped[int] = mapped_column()
    wrong: Mapped[int] = mapped_column()
    accuracy: Mapped[float] = mapped_column()

    wrong_words: Mapped[list[dict]] = mapped_column(JSON)

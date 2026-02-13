"""SQLModel veri modelleri."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Kullanıcı oturumu ────────────────────────────────────────────────
class UserSession(SQLModel, table=True):
    __tablename__ = "user_sessions"

    id: str = Field(primary_key=True, max_length=64)
    created_at: datetime = Field(default_factory=_now)


# ── Mesaj ─────────────────────────────────────────────────────────────
class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(max_length=64, index=True)
    role: str = Field(max_length=10)  # "user" | "bot"
    text: str
    category: Optional[str] = Field(default=None, max_length=50)
    confidence: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=_now)


# ── Destek talebi (Ticket) ───────────────────────────────────────────
class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(max_length=64, index=True)
    original_text: str
    predicted_category: Optional[str] = Field(default=None, max_length=50)
    confidence: Optional[float] = Field(default=None)
    status: str = Field(default="Açık", max_length=20)  # Açık | İşlemde | Çözüldü
    admin_note: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

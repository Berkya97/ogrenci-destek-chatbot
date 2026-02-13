"""Admin panel endpoint'leri – HTTP Basic Auth ile korumalı."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from sqlmodel import Session, func, select

from backend.app.config import ADMIN_PASSWORD
from backend.app.db import get_session
from backend.app.models import Message, Ticket

router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBasic()


# ── Yetkilendirme ────────────────────────────────────────────────────
def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Admin şifresini doğrular. Kullanıcı adı 'admin' olmalıdır."""
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        ADMIN_PASSWORD.encode("utf-8"),
    )
    correct_username = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        b"admin",
    )
    if not (correct_password and correct_username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz kimlik bilgileri",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ── Şemalar ───────────────────────────────────────────────────────────
class TicketUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(Açık|İşlemde|Çözüldü)$")
    admin_note: Optional[str] = Field(None, max_length=2000)


class TicketOut(BaseModel):
    id: int
    session_id: str
    original_text: str
    predicted_category: Optional[str]
    confidence: Optional[float]
    status: str
    admin_note: Optional[str]
    created_at: str
    updated_at: str


# ── Ticket listeleme ──────────────────────────────────────────────────
@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    status_filter: Optional[str] = None,
    _admin: str = Depends(verify_admin),
    session: Session = Depends(get_session),
) -> list[TicketOut]:
    """Tüm destek taleplerini listeler. İsteğe bağlı durum filtresi."""
    query = select(Ticket).order_by(Ticket.created_at.desc())  # type: ignore[union-attr]
    if status_filter:
        query = query.where(Ticket.status == status_filter)

    tickets = session.exec(query).all()
    return [
        TicketOut(
            id=t.id,  # type: ignore[arg-type]
            session_id=t.session_id,
            original_text=t.original_text,
            predicted_category=t.predicted_category,
            confidence=t.confidence,
            status=t.status,
            admin_note=t.admin_note,
            created_at=t.created_at.isoformat() if t.created_at else "",
            updated_at=t.updated_at.isoformat() if t.updated_at else "",
        )
        for t in tickets
    ]


# ── Ticket güncelleme ────────────────────────────────────────────────
@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    body: TicketUpdate,
    _admin: str = Depends(verify_admin),
    session: Session = Depends(get_session),
) -> TicketOut:
    """Belirli bir destek talebinin durumunu veya notunu günceller.

    Durum veya not değiştiğinde ilgili oturuma bot mesajı gönderir,
    böylece öğrenci sohbet ekranında güncellemeyi anında görür.
    """
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Talep bulunamadı.")

    status_changed = body.status is not None and body.status != ticket.status
    note_changed = body.admin_note is not None and body.admin_note != ticket.admin_note

    if body.status is not None:
        ticket.status = body.status
    if body.admin_note is not None:
        ticket.admin_note = body.admin_note

    ticket.updated_at = datetime.now(timezone.utc)
    session.add(ticket)

    # ── Öğrenciye bildirim mesajı oluştur ─────────────────────────
    if status_changed or note_changed:
        parts: list[str] = [f"📋 Talep güncellendi – TCK-{ticket.id}"]
        if status_changed:
            parts.append(f"Yeni durum: {ticket.status}")
        if note_changed and ticket.admin_note:
            parts.append(f"Admin notu: {ticket.admin_note}")
        notification_text = "\n".join(parts)

        bot_msg = Message(
            session_id=ticket.session_id,
            role="bot",
            text=notification_text,
            category=ticket.predicted_category,
        )
        session.add(bot_msg)

    session.commit()
    session.refresh(ticket)

    return TicketOut(
        id=ticket.id,  # type: ignore[arg-type]
        session_id=ticket.session_id,
        original_text=ticket.original_text,
        predicted_category=ticket.predicted_category,
        confidence=ticket.confidence,
        status=ticket.status,
        admin_note=ticket.admin_note,
        created_at=ticket.created_at.isoformat() if ticket.created_at else "",
        updated_at=ticket.updated_at.isoformat() if ticket.updated_at else "",
    )


# ── İstatistikler ────────────────────────────────────────────────────
@router.get("/stats")
def get_stats(
    _admin: str = Depends(verify_admin),
    session: Session = Depends(get_session),
) -> dict:
    """Basit istatistikler: toplam talep, durum dağılımı."""
    total = session.exec(select(func.count(Ticket.id))).one()

    status_counts = {}
    for s in ("Açık", "İşlemde", "Çözüldü"):
        count = session.exec(
            select(func.count(Ticket.id)).where(Ticket.status == s)
        ).one()
        status_counts[s] = count

    category_counts = {}
    rows = session.exec(
        select(Ticket.predicted_category, func.count(Ticket.id))
        .group_by(Ticket.predicted_category)
    ).all()
    for cat, cnt in rows:
        category_counts[cat or "Bilinmiyor"] = cnt

    return {
        "total_tickets": total,
        "by_status": status_counts,
        "by_category": category_counts,
    }

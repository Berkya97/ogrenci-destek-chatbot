"""Öğrenci sohbet endpoint'leri."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from backend.app.config import CONFIDENCE_THRESHOLD
from backend.app.db import get_session
from backend.app.knowledge.retriever import knowledge_retriever
from backend.app.models import Message, Ticket, UserSession
from backend.app.nlp.classifier import classifier

logger = logging.getLogger("ogrenci_destek.chat")

router = APIRouter(prefix="/api/chat", tags=["chat"])

# ── Bilgi tabanı eşik değeri ──────────────────────────────────────────
KNOWLEDGE_SCORE_THRESHOLD: float = 0.22


# ── Request / Response şemaları ───────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=64)
    text: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply_text: str
    category: str
    confidence: float
    ticket_id: Optional[str] = None


# ── Özel konu algılama (keyword-based) ────────────────────────────────
_SPECIFIC_TOPICS: dict[str, list[str]] = {
    "staj": ["staj mı", "staj mi", "staj değil", "staj mıdır", "staj midir", "bu staj"],
    "devamsızlık": ["devamsızlık", "devamsizlik", "devam zorunluluğu", "devam zorunlulugu", "devamsızlık sınırı", "gelmezse", "katılım zorunlu"],
    "puantaj": ["puantaj", "puantaj formu", "puantaj ne zaman"],
    "ara_rapor": ["ara rapor", "ara raporu"],
    "uygulama_raporu": ["uygulama raporu", "uygulama rapor"],
}

_SPECIFIC_ANSWERS: dict[str, str] = {
    "staj": (
        "Bu program bir staj DEĞİLDİR.\n\n"
        "İşletmede Mesleki Eğitim, son dönemde alınan zorunlu bir derstir. "
        "Öğrenci haftanın 5 günü işletmede çalışır ve %90 devam zorunluluğu vardır. "
        "Stajdan farklı olarak; ders notu verilir, devamsızlık takibi yapılır "
        "ve başarısızlık durumunda ders tekrar alınır.\n\n"
        "Kaynak: İşletmede Mesleki Eğitim sunumu"
    ),
    "devamsızlık": (
        "Devam Zorunluluğu:\n\n"
        "• Öğrencinin toplam eğitim süresinin en az %90'ına katılması zorunludur.\n"
        "• Mazeretsiz ardışık 3 gün devamsızlık yapan öğrenci başarısız sayılır.\n"
        "• İzin/mazeret süresi toplam eğitim süresinin %10'unu geçemez.\n"
        "• Devamsızlık durumunda işletme sorumlusu ve koordinatör bilgilendirilmelidir.\n\n"
        "Kaynak: İşletmede Mesleki Eğitim sunumu"
    ),
    "puantaj": (
        "Puantaj Formu:\n\n"
        "• Her ayın 1-7'si arasında bir önceki aya ait puantaj formu teslim edilmelidir.\n"
        "• Form, işletme yetkilisi tarafından onaylanmış olmalıdır.\n"
        "• Puantaj formunda günlük çalışma saatleri ve devam durumu yer alır.\n"
        "• Geç teslim edilen formlar değerlendirmeye alınmayabilir.\n\n"
        "Kaynak: İşletmede Mesleki Eğitim sunumu"
    ),
    "ara_rapor": (
        "Ara Rapor:\n\n"
        "• Eğitim süresinin ortasında (genellikle 6-8. hafta) ara rapor teslim edilir.\n"
        "• Raporda yapılan işler, öğrenilen beceriler ve gözlemler yer almalıdır.\n"
        "• İşletme danışmanı ve akademik danışman tarafından değerlendirilir.\n"
        "• Zamanında teslim edilmemesi not kırılmasına neden olabilir.\n\n"
        "Kaynak: İşletmede Mesleki Eğitim sunumu"
    ),
    "uygulama_raporu": (
        "Uygulama Raporu:\n\n"
        "• Eğitim sonunda hazırlanan kapsamlı bir değerlendirme raporudur.\n"
        "• İşletmede yapılan tüm faaliyetler, kazanılan yetkinlikler ve "
        "öz değerlendirme bölümlerini içermelidir.\n"
        "• Son teslim tarihine uyulmalıdır – geç teslim kabul edilmez.\n"
        "• Hem işletme danışmanı hem akademik danışman onayı gereklidir.\n\n"
        "Kaynak: İşletmede Mesleki Eğitim sunumu"
    ),
}


def _detect_specific_topic(text: str) -> str | None:
    """Metinde özel konu anahtar kelimeleri arar."""
    lower = text.lower()
    for topic, keywords in _SPECIFIC_TOPICS.items():
        if any(kw in lower for kw in keywords):
            return topic
    return None


def _build_grounded_reply(query: str, chunks: list[dict]) -> str:
    """
    Retrieval sonuçlarından temellendirilmiş (grounded) bir cevap oluşturur.

    En iyi chunk'ları kısa ve öz bir Türkçe cevap olarak sunar.
    Çok kısa chunk'ları (sadece başlık) atlar ve anlamlı içerik sunar.
    """
    if not chunks:
        return ""

    answer_parts: list[str] = []

    for chunk_data in chunks:
        chunk_text = chunk_data["chunk"]

        # Çok kısa chunk'ları atla (sadece başlık olabilir)
        if len(chunk_text) < 80:
            continue

        # Slayt numarasını satır başından temizle (ör: "2\nİş Yeri...")
        lines = chunk_text.split("\n")
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        chunk_text = "\n".join(lines).strip()

        if len(chunk_text) < 40:
            continue

        # Chunk metnini kısalt (çok uzunsa ilk 600 karakter)
        if len(chunk_text) > 600:
            cut = chunk_text[:600]
            last_period = cut.rfind(".")
            if last_period > 200:
                chunk_text = cut[: last_period + 1]
            else:
                chunk_text = cut + "…"

        answer_parts.append(chunk_text)

        # Toplam uzunluk sınırı
        if len("\n\n".join(answer_parts)) > 900:
            break

    if not answer_parts:
        # Hiçbir anlamlı chunk bulunamadı, en iyi chunk'ı olduğu gibi ver
        answer_parts.append(chunks[0]["chunk"])

    full_answer = "\n\n".join(answer_parts)

    # Kaynak bilgisi: chunk'ın geldiği dosyaya göre
    sources_used = {c.get("source", "pptx") for c in chunks if c["score"] > 0}
    if "docx" in sources_used:
        full_answer += "\n\nKaynak: İşletmede Mesleki Eğitim – SSS Belgesi"
    else:
        full_answer += "\n\nKaynak: İşletmede Mesleki Eğitim sunumu"
    return full_answer


# ── Mesaj gönderme endpoint'i ─────────────────────────────────────────
@router.post("/message", response_model=ChatResponse)
def send_message(
    body: ChatRequest,
    session: Session = Depends(get_session),
) -> ChatResponse:
    """
    Öğrenciden gelen mesajı işler:
    1. Oturum yoksa oluşturur.
    2. Mesajı veritabanına kaydeder.
    3. Özel konu algılama (staj, devamsızlık, puantaj vb.)
    4. Bilgi tabanından arama (RAG-lite)
    5. NLP ile kategori tahmini → FAQ veya ticket.
    """
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Mesaj boş olamaz.")

    # Oturum oluştur / kontrol et
    existing = session.get(UserSession, body.session_id)
    if not existing:
        session.add(UserSession(id=body.session_id))
        session.commit()

    # Kullanıcı mesajını kaydet (NLP tahmini de eklenir)
    category, confidence = classifier.predict(text)

    user_msg = Message(
        session_id=body.session_id,
        role="user",
        text=text,
        category=category,
        confidence=confidence,
    )
    session.add(user_msg)

    ticket_id: str | None = None

    # ── Adım 1: Özel konu algılama ───────────────────────────────
    specific_topic = _detect_specific_topic(text)
    if specific_topic and specific_topic in _SPECIFIC_ANSWERS:
        reply_text = _SPECIFIC_ANSWERS[specific_topic]
        reply_category = "Belge"
        reply_confidence = 0.95
        logger.info("Özel konu algılandı: %s", specific_topic)

    # ── Adım 2: Bilgi tabanından arama (RAG-lite) ────────────────
    elif knowledge_retriever.is_ready:
        results = knowledge_retriever.retrieve(text, top_k=3)
        best_score = results[0]["score"] if results else 0.0

        if best_score >= KNOWLEDGE_SCORE_THRESHOLD:
            reply_text = _build_grounded_reply(text, results)
            reply_category = "Belge"
            reply_confidence = best_score
            logger.info(
                "Bilgi tabanından cevap (skor=%.4f, slayt=%s)",
                best_score,
                results[0].get("slide_number"),
            )
        else:
            # Bilgi tabanında yeterli eşleşme yok → NLP akışına düş
            reply_text, reply_category, reply_confidence, ticket_id = (
                _fallback_nlp_flow(text, category, confidence, body.session_id, session)
            )
    else:
        # Retriever hazır değil → NLP akışına düş
        reply_text, reply_category, reply_confidence, ticket_id = (
            _fallback_nlp_flow(text, category, confidence, body.session_id, session)
        )

    # Bot mesajını kaydet
    bot_msg = Message(
        session_id=body.session_id,
        role="bot",
        text=reply_text,
        category=reply_category,
        confidence=reply_confidence,
    )
    session.add(bot_msg)
    session.commit()

    return ChatResponse(
        reply_text=reply_text,
        category=reply_category,
        confidence=round(reply_confidence, 4),
        ticket_id=ticket_id,
    )


def _fallback_nlp_flow(
    text: str,
    category: str,
    confidence: float,
    session_id: str,
    session: Session,
) -> tuple[str, str, float, str | None]:
    """
    Mevcut NLP akışı: FAQ yüksek güvenle cevap, düşükse ticket oluştur.

    Returns:
        (reply_text, category, confidence, ticket_id)
    """
    ticket_id: str | None = None

    if confidence >= CONFIDENCE_THRESHOLD:
        reply_text = classifier.get_faq_answer(category)
    else:
        # Destek talebi oluştur
        ticket = Ticket(
            session_id=session_id,
            original_text=text,
            predicted_category=category,
            confidence=confidence,
            status="Açık",
        )
        session.add(ticket)
        session.flush()  # id ataması için
        ticket_id = f"TCK-{ticket.id}"
        reply_text = (
            f"Talebini aldım ✅\n"
            f"Takip numaran: {ticket_id}\n"
            f"En kısa sürede dönüş yapılacak."
        )

    return reply_text, category, confidence, ticket_id


# ── Sohbet geçmişi ───────────────────────────────────────────────────
@router.get("/history")
def get_history(
    session_id: str,
    after_id: Optional[int] = None,
    session: Session = Depends(get_session),
) -> list[dict]:
    """
    Belirli bir oturumun mesaj geçmişini döndürür.

    after_id verilirse yalnızca o id'den büyük mesajları döndürür (polling).
    Sonuçlar id'ye göre artan sırada sıralanır.
    """
    query = select(Message).where(Message.session_id == session_id)
    if after_id is not None:
        query = query.where(Message.id > after_id)  # type: ignore[operator]
    query = query.order_by(Message.id.asc())  # type: ignore[union-attr]

    messages = session.exec(query).all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "text": m.text,
            "category": m.category,
            "confidence": m.confidence,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


# ── Kategoriler ───────────────────────────────────────────────────────
@router.get("/categories")
def get_categories() -> list[str]:
    """Mevcut kategorileri döndürür."""
    return classifier.categories

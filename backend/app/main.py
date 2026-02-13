"""
Öğrenci Destek – Ana FastAPI uygulaması.

Çalıştırma:
    uvicorn backend.app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.db import create_db_and_tables
from backend.app.knowledge.retriever import knowledge_retriever
from backend.app.nlp.classifier import classifier
from backend.app.routes.admin import router as admin_router
from backend.app.routes.chat import router as chat_router
from backend.app.routes.knowledge import router as knowledge_router

logger = logging.getLogger("ogrenci_destek")

STATIC_DIR = Path(__file__).parent / "static"


# ── Yaşam döngüsü ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlatılırken DB, NLP modeli ve bilgi tabanını hazırla."""
    logger.info("Veritabanı tabloları oluşturuluyor...")
    create_db_and_tables()

    logger.info("NLP sınıflandırıcı eğitiliyor...")
    classifier.train()

    logger.info("Bilgi tabanı (PPTX) yükleniyor...")
    try:
        knowledge_retriever.build()
    except Exception:
        logger.exception("Bilgi tabanı yüklenemedi – RAG devre dışı.")

    logger.info("Uygulama hazır!")

    yield  # Uygulama çalışıyor

    logger.info("Uygulama kapatılıyor.")


# ── FastAPI uygulaması ────────────────────────────────────────────────
app = FastAPI(
    title="Öğrenci Destek",
    description="Öğrenci destek chatbotu – MVP + RAG-lite bilgi tabanı",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS (geliştirme ortamı için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(knowledge_router)

# Statik dosyalar
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Sayfa yönlendirmeleri ─────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_index():
    """Ana sayfa – öğrenci sohbet arayüzü."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin", include_in_schema=False)
async def serve_admin():
    """Admin paneli sayfası."""
    return FileResponse(STATIC_DIR / "admin.html")

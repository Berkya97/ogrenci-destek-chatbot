"""Uygulama yapılandırması – .env dosyasından okunur."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# .env dosyasını yükle (proje kök dizininde)
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)

ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "degistir123")
APP_SECRET: str = os.getenv("APP_SECRET", secrets.token_hex(32))

# Veritabanı dosyası backend/ klasörü altında oluşturulur
DATABASE_URL: str = "sqlite:///" + str(
    Path(__file__).resolve().parents[1] / "ogrenci_destek.db"
)

# NLP eşik değeri – bu değerin üstündeyse FAQ cevabı verilir
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))

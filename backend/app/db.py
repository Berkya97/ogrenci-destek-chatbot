"""Veritabanı motoru ve oturum yönetimi."""

from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from backend.app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    """Tüm SQLModel tablolarını oluşturur."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI Depends için veritabanı oturumu üreteci."""
    with Session(engine) as session:
        yield session

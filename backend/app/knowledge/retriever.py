"""
TF-IDF tabanlı bilgi tabanı arama (retriever).

İlk çalıştırmada PPTX + DOCX dosyalarından chunk'ları çıkarır, TF-IDF
modeli oluşturur ve sonuçları diske önbellek olarak kaydeder.
Sonraki çalıştırmalarda önbellekten yükler.

Kullanım:
    from backend.app.knowledge.retriever import knowledge_retriever
    results = knowledge_retriever.retrieve("staj mı?")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TypedDict

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.app.knowledge.pptx_loader import (
    Chunk,
    load_and_chunk_docx,
    load_and_chunk_pptx,
)

logger = logging.getLogger("ogrenci_destek.knowledge.retriever")

# ── Sabitler ──────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_CACHE_DIR = _HERE / "cache"
_CACHE_VECTORIZER = _CACHE_DIR / "tfidf_vectorizer.pkl"
_CACHE_MATRIX = _CACHE_DIR / "tfidf_matrix.pkl"
_CACHE_CHUNKS = _CACHE_DIR / "chunks.pkl"

# Proje kök dizini (dayı site/)
_PROJECT_ROOT = _HERE.parents[2]

# Varsayılan dosya yolları
DEFAULT_PPTX_PATH = _PROJECT_ROOT / "000İŞLETMEDE MESLEKİ EĞİTİM_SUNUM.pptx"
DEFAULT_DOCX_PATH = _PROJECT_ROOT / "0000SSS.docx"


# ── Sonuç tipi ────────────────────────────────────────────────────────
class RetrievalResult(TypedDict):
    chunk: str
    score: float
    source: str
    slide_number: int | None


# ── Retriever sınıfı ─────────────────────────────────────────────────
class KnowledgeRetriever:
    """PPTX + DOCX bilgi tabanı üzerinde TF-IDF tabanlı arama."""

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix: np.ndarray | None = None  # sparse olabilir
        self._chunks: list[Chunk] = []
        self._ready = False

    # ── Hazır mı? ─────────────────────────────────────────────────
    @property
    def is_ready(self) -> bool:
        return self._ready

    # ── Oluştur / yükle ───────────────────────────────────────────
    def build(
        self,
        pptx_path: str | Path | None = None,
        docx_path: str | Path | None = None,
        force: bool = False,
    ) -> None:
        """
        Bilgi tabanını oluşturur veya önbellekten yükler.

        PPTX ve DOCX dosyalarından chunk'ları birleştirerek tek bir
        TF-IDF vektör alanı oluşturur.

        Args:
            pptx_path: PPTX dosya yolu. None ise varsayılan kullanılır.
            docx_path: DOCX dosya yolu. None ise varsayılan kullanılır.
            force:     True ise önbelleği yok sayar ve yeniden oluşturur.
        """
        pptx_path = Path(pptx_path) if pptx_path else DEFAULT_PPTX_PATH
        docx_path = Path(docx_path) if docx_path else DEFAULT_DOCX_PATH

        # Önbellek varsa ve force değilse yükle
        if not force and self._cache_exists():
            self._load_cache()
            return

        all_chunks: list[Chunk] = []

        # ── PPTX'ten chunk'ları çıkar ─────────────────────────────
        if pptx_path.exists():
            logger.info("PPTX'ten bilgi tabanı oluşturuluyor: %s", pptx_path.name)
            pptx_chunks = load_and_chunk_pptx(pptx_path)
            all_chunks.extend(pptx_chunks)
        else:
            logger.warning("PPTX dosyası bulunamadı: %s", pptx_path)

        # ── DOCX'ten chunk'ları çıkar ─────────────────────────────
        if docx_path.exists():
            logger.info("DOCX'ten bilgi tabanı oluşturuluyor: %s", docx_path.name)
            docx_chunks = load_and_chunk_docx(
                docx_path, start_index=len(all_chunks),
            )
            all_chunks.extend(docx_chunks)
        else:
            logger.warning("DOCX dosyası bulunamadı: %s", docx_path)

        if not all_chunks:
            logger.warning("Hiçbir kaynaktan metin çıkarılamadı – Retriever devre dışı.")
            return

        self._chunks = all_chunks

        # TF-IDF vektörleştirici
        texts = [c["text"] for c in self._chunks]
        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            max_features=10_000,
            sublinear_tf=True,
            stop_words=_TURKISH_STOP_WORDS,
        )
        self._matrix = self._vectorizer.fit_transform(texts)
        self._ready = True

        # Önbelleğe kaydet
        self._save_cache()
        logger.info(
            "Bilgi tabanı hazır – %d parça (%d PPTX + %d DOCX), %d özellik.",
            len(self._chunks),
            sum(1 for c in self._chunks if c.get("source") == "pptx"),
            sum(1 for c in self._chunks if c.get("source") == "docx"),
            self._matrix.shape[1],
        )

    # ── Arama ─────────────────────────────────────────────────────
    def retrieve(
        self, query: str, top_k: int = 3
    ) -> list[RetrievalResult]:
        """
        Sorguya en yakın chunk'ları döndürür.

        Args:
            query: Kullanıcı sorusu.
            top_k: Döndürülecek sonuç sayısı.

        Returns:
            RetrievalResult listesi (en yüksek skordan düşüğe sıralı).
        """
        if not self._ready or self._vectorizer is None or self._matrix is None:
            return []

        query = query.strip()
        if not query:
            return []

        # Sorguyu vektörleştir
        query_vec = self._vectorizer.transform([query])

        # Kosinüs benzerliği (TF-IDF matris zaten L2-normalleştirilmiş)
        scores = (self._matrix @ query_vec.T).toarray().flatten()

        if len(scores) == 0:
            return []

        # En yüksek top_k indeks
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: list[RetrievalResult] = []
        for i in top_indices:
            score = float(scores[i])
            if score <= 0:
                continue
            chunk = self._chunks[i]
            results.append(
                RetrievalResult(
                    chunk=chunk["text"],
                    score=round(score, 4),
                    source=chunk.get("source", "pptx"),
                    slide_number=chunk.get("slide_number"),
                )
            )

        return results

    # ── Önbelleği yenile ──────────────────────────────────────────
    def refresh(
        self,
        pptx_path: str | Path | None = None,
        docx_path: str | Path | None = None,
    ) -> None:
        """Önbelleği siler ve bilgi tabanını yeniden oluşturur."""
        self._clear_cache()
        self._ready = False
        self.build(pptx_path=pptx_path, docx_path=docx_path, force=True)

    # ── Önbellek işlemleri ────────────────────────────────────────
    def _cache_exists(self) -> bool:
        return (
            _CACHE_VECTORIZER.exists()
            and _CACHE_MATRIX.exists()
            and _CACHE_CHUNKS.exists()
        )

    def _save_cache(self) -> None:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._vectorizer, _CACHE_VECTORIZER)
        joblib.dump(self._matrix, _CACHE_MATRIX)
        joblib.dump(self._chunks, _CACHE_CHUNKS)
        logger.info("Bilgi tabanı önbelleğe kaydedildi: %s", _CACHE_DIR)

    def _load_cache(self) -> None:
        try:
            self._vectorizer = joblib.load(_CACHE_VECTORIZER)
            self._matrix = joblib.load(_CACHE_MATRIX)
            self._chunks = joblib.load(_CACHE_CHUNKS)
            self._ready = True
            logger.info(
                "Bilgi tabanı önbellekten yüklendi – %d parça.", len(self._chunks)
            )
        except Exception:
            logger.exception("Önbellek yüklenemedi, yeniden oluşturulacak.")
            self._ready = False

    def _clear_cache(self) -> None:
        for p in (_CACHE_VECTORIZER, _CACHE_MATRIX, _CACHE_CHUNKS):
            if p.exists():
                p.unlink()
        logger.info("Önbellek temizlendi.")


# ── Türkçe stop-words (temel) ────────────────────────────────────────
_TURKISH_STOP_WORDS: list[str] = [
    "bir", "ve", "bu", "da", "de", "ile", "için", "ama", "ancak",
    "veya", "ya", "hem", "ne", "kadar", "gibi", "daha", "en",
    "çok", "her", "bazı", "tüm", "bütün", "olan", "olarak",
    "var", "yok", "ben", "sen", "biz", "siz", "onlar",
    "mi", "mı", "mu", "mü", "dir", "dır", "dur", "dür",
    "den", "dan", "ten", "tan", "nin", "nın", "nun", "nün",
    "ın", "in", "un", "ün", "ler", "lar", "leri", "ları",
]

# ── Modül düzeyinde tekil örnek ───────────────────────────────────────
knowledge_retriever = KnowledgeRetriever()

"""Bilgi tabanı arama endpoint'leri – hata ayıklama ve test amaçlı."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.knowledge.retriever import knowledge_retriever

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/search")
def search_knowledge(
    q: str = Query(..., min_length=1, max_length=500, description="Arama sorgusu"),
    top_k: int = Query(3, ge=1, le=10, description="Döndürülecek sonuç sayısı"),
) -> dict:
    """
    Bilgi tabanında arama yapar.

    PPTX'ten çıkarılan parçalar arasında TF-IDF kosinüs benzerliğine göre
    en yakın top_k sonucu döndürür.  Hata ayıklama için kullanılır.
    """
    if not knowledge_retriever.is_ready:
        return {"query": q, "results": [], "message": "Bilgi tabanı henüz hazır değil."}

    results = knowledge_retriever.retrieve(q, top_k=top_k)

    return {
        "query": q,
        "results": [
            {
                "chunk": r["chunk"],
                "score": r["score"],
                "source": r["source"],
                "slide_number": r["slide_number"],
            }
            for r in results
        ],
    }

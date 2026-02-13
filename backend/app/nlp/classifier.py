"""
TF-IDF + LinearSVC tabanlı metin sınıflandırıcı.

Başlangıç verisiyle eğitilir; güven skoru döndürür.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC

from backend.app.nlp.seed_data import CATEGORY_EXAMPLES, FAQ_TEMPLATES


class QuestionClassifier:
    """Öğrenci sorularını kategorilere ayıran sınıflandırıcı."""

    def __init__(self) -> None:
        self._label_encoder = LabelEncoder()
        self._pipeline: Pipeline | None = None
        self._is_trained = False

    # ── Eğitim ────────────────────────────────────────────────────────
    def train(self) -> None:
        """Seed verisiyle modeli eğitir."""
        texts: list[str] = []
        labels: list[str] = []

        for category, examples in CATEGORY_EXAMPLES.items():
            for example in examples:
                texts.append(example)
                labels.append(category)

        encoded_labels = self._label_encoder.fit_transform(labels)

        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                max_features=5000,
                sublinear_tf=True,
            )),
            ("clf", LinearSVC(
                C=1.0,
                max_iter=10000,
                class_weight="balanced",
            )),
        ])

        self._pipeline.fit(texts, encoded_labels)
        self._is_trained = True

    # ── Tahmin ────────────────────────────────────────────────────────
    def predict(self, text: str) -> tuple[str, float]:
        """
        Metin için kategori ve güven skoru döndürür.

        Güven hesaplama: En yüksek skor ile ikinci en yüksek skor arasındaki
        farka sigmoid uygulayarak [0, 1] aralığına ölçekler.
        Böylece ayrım net olduğunda yüksek, belirsizde düşük güven verir.

        Returns:
            (category, confidence) – confidence [0, 1] aralığında.
        """
        if not self._is_trained or self._pipeline is None:
            self.train()

        # decision_function → her sınıf için skor
        decision_scores = self._pipeline.decision_function([text])[0]

        if decision_scores.ndim == 0:
            # İkili sınıf durumu (burada olmaz ama güvenlik için)
            confidence = float(1 / (1 + np.exp(-abs(decision_scores))))
            predicted_idx = int(decision_scores > 0)
        else:
            predicted_idx = int(np.argmax(decision_scores))

            # Margin-based confidence: en yüksek ile ikinci en yüksek skor farkı
            sorted_scores = np.sort(decision_scores)[::-1]
            margin = sorted_scores[0] - sorted_scores[1]

            # Sigmoid ile [0, 1] aralığına ölçekle (k=2 ölçek faktörü)
            confidence = float(1 / (1 + np.exp(-2.0 * margin)))

        category = self._label_encoder.inverse_transform([predicted_idx])[0]
        return str(category), round(confidence, 4)

    # ── FAQ cevabı ────────────────────────────────────────────────────
    @staticmethod
    def get_faq_answer(category: str) -> str:
        """Kategori için önceden tanımlı FAQ cevabını döndürür."""
        return FAQ_TEMPLATES.get(category, FAQ_TEMPLATES["Diğer"])

    @property
    def categories(self) -> list[str]:
        """Mevcut kategorileri döndürür."""
        return list(CATEGORY_EXAMPLES.keys())


# Modül düzeyinde tekil (singleton) sınıflandırıcı örneği
classifier = QuestionClassifier()

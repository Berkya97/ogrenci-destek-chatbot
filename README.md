# Öğrenci Destek – Chatbot (MVP)

WhatsApp benzeri sohbet arayüzü üzerinden öğrenci sorularını **otomatik kategorize eden** ve FAQ cevapları veren bir destek sistemi.

## Özellikler

- **Akıllı Soru Sınıflandırma**: TF-IDF + LinearSVC ile Türkçe metin sınıflandırma
- **4 Kategori**: Akademik, Teknik, Ödeme, Diğer
- **Otomatik FAQ Cevaplama**: Yüksek güven skorunda anında cevap
- **Destek Talebi Sistemi**: Düşük güven skorunda otomatik ticket oluşturma
- **Admin Paneli**: Ticket yönetimi, durum güncelleme, istatistikler
- **WhatsApp Tarzı UI**: Modern, responsive sohbet arayüzü

## Hızlı Başlangıç

### 1. Gereksinimleri Yükleyin

```bash
cd "dosya yolu"
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Ortam Değişkenlerini Ayarlayın

`.env.example` dosyasını `.env` olarak kopyalayın ve değerleri güncelleyin:

```bash
cp .env.example .env
```

```env
ADMIN_PASSWORD=guclu-bir-sifre
APP_SECRET=rastgele-gizli-anahtar
CONFIDENCE_THRESHOLD=0.65
```

### 3. Uygulamayı Başlatın

```bash
uvicorn backend.app.main:app --reload
```

Uygulama **http://127.0.0.1:8000** adresinde çalışacaktır.

### 4. Kullanım

| Sayfa | URL | Açıklama |
|-------|-----|----------|
| Sohbet | http://127.0.0.1:8000 | Öğrenci sohbet arayüzü |
| Admin | http://127.0.0.1:8000/admin | Ticket yönetimi (şifre gerekli) |
| API Docs | http://127.0.0.1:8000/docs | Swagger API dokümantasyonu |

**Admin Girişi**: Kullanıcı adı `admin`, şifre `.env` dosyasındaki `ADMIN_PASSWORD` değeri.

## Örnek API İstekleri (curl)

### Mesaj Gönderme

```bash
curl -X POST http://127.0.0.1:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session-1", "text": "Ders kaydı nasıl yapılır?"}'
```

### Sohbet Geçmişi

```bash
curl http://127.0.0.1:8000/api/chat/history/test-session-1
```

### Kategorileri Listeleme

```bash
curl http://127.0.0.1:8000/api/chat/categories
```

### Ticketları Listeleme (Admin)

```bash
curl -u admin:degistir123 http://127.0.0.1:8000/api/admin/tickets
```

### Ticket Güncelleme (Admin)

```bash
curl -X PATCH http://127.0.0.1:8000/api/admin/tickets/1 \
  -u admin:degistir123 \
  -H "Content-Type: application/json" \
  -d '{"status": "Çözüldü", "admin_note": "Sorun giderildi."}'
```

### İstatistikler (Admin)

```bash
curl -u admin:degistir123 http://127.0.0.1:8000/api/admin/stats
```

## Yeni Kategori / Soru Ekleme

1. `backend/app/nlp/seed_data.py` dosyasını açın.

2. `CATEGORY_EXAMPLES` sözlüğüne yeni kategori ve örnek sorular ekleyin:

```python
CATEGORY_EXAMPLES["Yeni Kategori"] = [
    "Örnek soru 1",
    "Örnek soru 2",
    # En az 10-15 örnek ekleyin
]
```

3. `FAQ_TEMPLATES` sözlüğüne aynı anahtarla bir FAQ cevabı ekleyin:

```python
FAQ_TEMPLATES["Yeni Kategori"] = "Bu konuda yardımcı olabilirim! ..."
```

4. Uygulamayı yeniden başlatın – model otomatik olarak yeni verilerle eğitilecektir.

> **İpucu**: Her kategori için en az 15-20 örnek soru eklemek sınıflandırma doğruluğunu artırır.

## Bilgi Tabanı (PPTX – RAG-lite)

Sistem, iki kaynak dosyayı bilgi tabanı olarak kullanır:
- **`000İŞLETMEDE MESLEKİ EĞİTİM_SUNUM.pptx`** – Sunum slaytları (14 slayt → 18 chunk)
- **`0000SSS.docx`** – Sıkça Sorulan Sorular (55 soru-cevap çifti)

Öğrenci soruları önce bu bilgi tabanında aranır; yeterli eşleşme bulunursa kaynak içeriğe dayalı
temellendirilmiş (grounded) cevap verilir, ticket açılmaz.

### Nasıl Çalışır?

1. Uygulama başlatıldığında PPTX'ten slayt metinleri, DOCX'ten soru-cevap çiftleri çıkarılır.
2. PPTX metinleri ~550 karakterlik örtüşen parçalara bölünür; DOCX'teki her QA çifti ayrı bir chunk olur.
3. Tüm parçalar (18 PPTX + 55 DOCX = 73 chunk) TF-IDF ile vektörleştirilir ve önbelleğe kaydedilir.
4. Her soru geldiğinde kosinüs benzerliği ile en yakın parçalar bulunur.
5. Skor ≥ 0.22 ise bilgi tabanından grounded cevap verilir; aksi halde FAQ / ticket akışına düşülür.

### Bilgi Tabanını Güncelleme / Yenileme

PPTX dosyasını güncelledikten sonra önbelleği temizlemeniz gerekir:

```bash
# Yöntem 1: Cache klasörünü silin ve uygulamayı yeniden başlatın
rm -rf backend/app/knowledge/cache/
uvicorn backend.app.main:app --reload

# Yöntem 2 (Windows):
del /s /q backend\app\knowledge\cache\
uvicorn backend.app.main:app --reload
```

Uygulama sonraki başlatmada PPTX'i yeniden işleyecek ve yeni önbellek oluşturacaktır.

### Debug Endpoint'i

Bilgi tabanı aramasını test etmek için:

```bash
curl "http://127.0.0.1:8000/api/knowledge/search?q=puantaj%20ne%20zaman"
```

### Özel Konu Algılama

Aşağıdaki konularda anahtar kelime eşleşmesi ile doğrudan cevap verilir:

| Konu | Tetikleyici Kelimeler |
|------|----------------------|
| Staj mı? | "staj mı", "staj mi", "bu staj" |
| Devamsızlık | "devamsızlık", "devam zorunluluğu" |
| Puantaj | "puantaj", "puantaj formu" |
| Ara Rapor | "ara rapor", "ara raporu" |
| Uygulama Raporu | "uygulama raporu" |

## Proje Yapısı

```
repo/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI uygulaması
│   │   ├── config.py           # Yapılandırma (.env)
│   │   ├── db.py               # Veritabanı motoru
│   │   ├── models.py           # SQLModel veri modelleri
│   │   ├── knowledge/          # 🆕 Bilgi tabanı (RAG-lite)
│   │   │   ├── pptx_loader.py  # PPTX metin çıkarma & parçalama
│   │   │   ├── retriever.py    # TF-IDF vektörleştirici & arama
│   │   │   └── cache/          # Önbellek (.pkl dosyaları)
│   │   ├── nlp/
│   │   │   ├── classifier.py   # TF-IDF + LinearSVC sınıflandırıcı
│   │   │   └── seed_data.py    # Örnek sorular ve FAQ şablonları
│   │   ├── routes/
│   │   │   ├── chat.py         # Sohbet API endpoint'leri
│   │   │   ├── admin.py        # Admin API endpoint'leri
│   │   │   └── knowledge.py    # 🆕 Bilgi tabanı arama endpoint'i
│   │   └── static/
│   │       ├── index.html      # Öğrenci sohbet arayüzü
│   │       ├── admin.html      # Admin paneli
│   │       ├── styles.css      # Tüm stiller
│   │       ├── app.js          # Sohbet JavaScript
│   │       └── admin.js        # Admin JavaScript
├── 000İŞLETMEDE MESLEKİ EĞİTİM_SUNUM.pptx  # 🆕 Bilgi tabanı: sunum
├── 0000SSS.docx                              # 🆕 Bilgi tabanı: SSS belgesi
├── requirements.txt
├── .env.example
└── README.md
```

## Teknoloji

- **Backend**: Python 3.12, FastAPI, Uvicorn
- **Veritabanı**: SQLite (SQLModel ORM)
- **NLP**: scikit-learn (TF-IDF Vectorizer + LinearSVC)
- **RAG-lite**: python-pptx + python-docx + TF-IDF kosinüs benzerliği (bilgi tabanı)
- **Frontend**: Vanilla HTML/CSS/JS
- **Auth**: HTTP Basic Authentication

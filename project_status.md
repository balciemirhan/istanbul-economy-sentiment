# İstanbul Ekonomi Analizi - Proje Durumu

## 🎯 Projenin Amacı
İstanbul'daki ekonomik gündemi X (Twitter) üzerinden takip edip, yöneticiye haftalık rapor sunmak.

## 📋 İş Akışı
1️⃣ **VERİ ÇEKME (Haftalık - Pazartesi)**
   └─ X'ten son 1 haftalık tweetleri çek ("İstanbul" + "ekonomi", "borsa", "ito" ve hashtagler)
2️⃣ **NLP ANALİZİ**
   └─ Her tweet'i 3 kategoriye ayır (Pozitif, Negatif, Nötr)
3️⃣ **VERİTABANI**
   └─ SQLite'e kaydet (Metin, tarih, etkileşimler, duygu skoru)
4️⃣ **DASHBOARD (UI)**
   └─ Grafiklerle görselleştir (Pasta grafik, trend, tweet listesi)
5️⃣ **HAFTALIK RAPOR (PDF)**
   └─ Yöneticiye özet sun

## Güncel Mimari

```text
┌─────────────────────────────────────────────────────────────┐
│                    GÜNCELLENMİŞ MİMARİ                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐         ┌─────────────────┐              │
│  │   X API      │─────────▶│  Python Script  │              │
│  │  (PAYG)      │  Haftalık│  + BERT Model   │              │
│  │              │   Veri   │                 │              │
│  └──────────────┘         └────────┬────────┘              │
│                                     │                        │
│                                     ▼                        │
│                              ┌──────────────┐               │
│                              │   SQLite     │               │
│                              │  (.db file)  │               │
│                              └──────┬───────┘               │
│                                     │                        │
│                                     ▼                        │
│                              ┌──────────────┐               │
│                              │   Dashboard  │               │
│                              │   (HTML/JS)  │               │
│                              └──────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Klasör Yapısı

```text
istanbul-ekonomi-analizi/       # Proje Kök Dizini
├── api/                        # Veri Toplama Katmanı (X API)
│   ├── __init__.py             # Modül tanımlayıcı
│   ├── scheduler.py            # Zamanlanmış görevler (Örn: Haftalık çalışma)
│   ├── tweet_fetcher.py        # Belirli konular/etiketler için tweet çekme
│   └── x_api_client.py         # X API bağlantı ayarları ve temel istekler
├── dashboard/                  # Kullanıcı Arayüzü (Web)
│   ├── api/                    # Frontend'e veri sunacak sunucu (Flask vb.)
│   └── frontend/               # HTML/JS ile görselleştirme paneli
├── database/                   # Veri Depolama Katmanı (SQLite)
│   ├── migrations/             # Veritabanı şema değişiklikleri (Alembic)
│   ├── __init__.py             # Modül tanımlayıcı
│   ├── db_manager.py           # Veritabanı okuma/yazma işlemleri (CRUD)
│   └── models.py               # Tablo yapıları (SQLAlchemy modelleri)
├── nlp/                        # Doğal Dil İşleme Katmanı
│   ├── __init__.py             # Modül tanımlayıcı
│   ├── irony_detector.py       # İroni ve kinaye tespiti
│   ├── sentiment_analyzer.py   # Duygu analizi (BERT Model)
│   └── text_cleaner.py         # Veri ön işleme (Noktalama, emoji temizliği)
├── reports/                    # Raporlama Katmanı
│   ├── __init__.py             # Modül tanımlayıcı
│   └── pdf_generator.py        # Analiz sonuçlarını PDF olarak dışa aktarma (fpdf2)
├── .env                        # Gizli çevresel değişkenler (API anahtarları vb.)
├── config.py                   # Proje geneli genel yapılandırma ve sabitler
├── main.py                     # Ana orkestrasyon (Tüm sistemi sırayla çalıştıran script)
├── project_status.md           # Proje mimarisi ve görev takibi dokümanı
└── requirements.txt            # Python bağımlılık listesi
```

## Tamamlanan Adımlar
- [x] Klasör yapısı oluşturuldu.
- [x] Gerekli tüm boş dosyalar (`__init__.py`, `main.py` dahil) yaratıldı.
- [x] `requirements.txt` hazırlandı ve bağımlılıklar (`pip install -r requirements.txt`) yüklendi.
- [x] Veritabanı modellerine (`models.py`) performans için indexler (dizinler) eklendi (`created_at` ve `sentiment`).

## Sıradaki Adımlar (Önerilen)
- [ ] Veritabanı modellerinin (`models.py`) ve veritabanı bağlantısının (`db_manager.py`) ayarlanması.
- [ ] API üzerinden veri çekme modüllerinin (`x_api_client.py`, `tweet_fetcher.py`) yazılması.
- [ ] Çekilen verilerin NLP klasöründeki modellerle (`sentiment_analyzer.py`) analiz edilmesi.
- [ ] Ana uygulamanın (`main.py`) içerisindeki pipeline'ın çalıştırılması.

# 📊 İstanbul Ekonomi Analizi (X/Twitter Sentiment Tracker)

Bu proje, İstanbul'daki ekonomik gündemi X (Twitter) üzerinden takip eden, gelişmiş Doğal Dil İşleme (NLP) yetenekleriyle halkın duygusunu analiz eden ve sonuçları dinamik bir web arayüzünde (Dashboard) sunan tam otomatik bir veri toplama sistemidir.

## 🎯 Projenin Amacı
Amacımız, finans ve ekonomi ile ilgili İstanbul tabanlı atılan tweetleri toplamak, analiz etmek ve genel olarak **"Halkın Ekonomik Algısı"nı (Sentiment)** Pozitif, Negatif veya Nötr olarak etiketlemektir. Yöneticiler için anlık veri takibi ve Excel raporlaması sunar.

---

## 🚀 Temel Özellikler

1. **X API v2 Entegrasyonu:** Gerçek zamanlı ve hatasız veri çekimi. Aylık kota koruması için geliştirilmiş Yerel Bütçe Takipçisi (Local Usage Monitor).
2. **Gelişmiş NLP Duygu Analizi:** HuggingFace `savasy/bert-base-turkish-sentiment-cased` Türkçe BERT modeli ile yüksek doğruluklu metin sınıflandırması.
3. **Kural Tabanlı İroni ve Ezme (Override) Motoru:** Türkçe argo, ironi ve siyasi isyanları kavrayabilmesi için modele eklenen manuel kurallar bütünü.
4. **Veritabanı (SQLite):** Çekilen verilerin hızlıca depolanması ve Dashboard için pagination (sayfalama) desteği ile sorunsuz okunması.
5. **Yönetici Paneli (Dashboard):** Dinamik kelime filtreleme ekleme, tarih/zaman seçimi yapabilme, kümülatif API limiti takibi ve tek tıkla Excel çıktısı alma imkanı.

---

## 🧠 Nasıl Çalışır? (Filtreler ve Kurallar)

Projenin en can alıcı noktası, spam veriyi eleyip sadece "kaliteli halk görüşünü" veritabanına almasıdır.

### A) Spam ve Kopya Haber Filtresi (Deduplication)
- **İlk 50 Karakter Kuralı:** Haber ajansları veya bot hesaplar aynı metni sonlarına farklı emojiler/linkler koyarak paylaşsa dahi sistem metnin ilk 50 karakterini alır.
- **Tarihsel Çapraz Kontrol:** Sistem sadece o an çekilen verilerde değil, **veritabanındaki geçmiş 7 günün verileriyle** de çapraz eşleşme yapar. Kopya haber veritabanına asla ikinci kez sızamaz.

### B) Metin Temizleyici (Text Cleaner)
- BERT modeline girmeden önce tweetler; URL'lerden, RT (Retweet) başlıklarından, kullanıcı etiketlerinden (@) ve anlamsız hashtag kalıntılarından agresif bir şekilde temizlenir. Finansal matematik (%, +, /) korunur.

### C) Duygu Analizi & Kural Tabanlı Karar (Sentiment Override)
- **Nötr Filtresi (%85 Güven):** Yapay zeka bir metnin pozitif mi negatif mi olduğundan %85 oranından daha az eminse (yani sıradan bir haberse), sistem onu otomatik olarak **Nötr** sayar.
- **Ekonomik İsyan Filtresi:** BERT modeli "zam" gibi kelimeleri genel dilde "maaş zammı" zannedip Pozitif skorlayabilir. Eğer metin içerisinde *"protesto", "eylem", "yürüyoruz", "açlık", "geçinemiyoruz", "pahalılık"* gibi kelimeler geçiyorsa, sistem BERT'i ezer ve zorla **Negatif** kararı verir.
- **İroni Tespiti:** Aşırı ünlem/soru işareti kullanımı ve ironik sözcükler yakalanırsa duygu zıtlaştırılır (Pozitif -> Negatif).

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Gereksinimler
- Python 3.8+
- X (Twitter) API Developer Hesabı ve Bearer Token

### 2. Kurulum
Terminalinizi açın ve projeyi bilgisayarınıza klonlayın:

```bash
# Projeyi klonlayın ve klasöre girin
git clone https://github.com/balciemirhan/istanbul-economy-sentiment.git
cd istanbul-economy-sentiment

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 3. Çevresel Değişkenler (Environment Variables)
Proje ana dizininde bir `.env` dosyası oluşturun ve X API anahtarınızı içine yapıştırın:
*(Not: .env dosyası güvenlik sebebiyle GitHub'a yüklenmeyecek şekilde .gitignore ile korunmuştur).*

```env
X_BEARER_TOKEN="BURAYA_API_TOKEN_GELECEK"
```

### 4. Çalıştırma
Yönetici panelini (Dashboard) başlatmak için ana dizinde şu komutu çalıştırın:

```bash
python -m dashboard.api.app
```
Tarayıcınızda `http://127.0.0.1:5000` adresine giderek sistemi kullanmaya başlayabilirsiniz. Sistem açıldığında otomatik olarak veritabanı tablolarını (yoksa) oluşturacaktır.

---

## 📁 Proje Yapısı

- `api/` -> X API bağlantı ayarları ve fetch algoritması.
- `nlp/` -> BERT modeli, ironi dedektörü, metin temizleyici ve override kuralları.
- `database/` -> SQLite yapılandırması ve geçmiş/kopya kontrol fonksiyonları.
- `dashboard/` -> Flask API, HTML/CSS yönetim ve izleme panelleri.
- `main.py` -> Analizi, veritabanını ve NLP'yi birleştiren ana tetikleyici boru hattı (Pipeline).

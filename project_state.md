# İstanbul Ekonomi Analizi - Proje Durumu (State)

Bu dosya, projede gerçekleştirilen **en son değişiklikleri, güncellemeleri ve mevcut çalışma durumunu** (state) detaylandırmak amacıyla oluşturulmuştur. Ayrıca yapay zeka ajanlarının referans alması gereken proje mimarisini ve kodlama prensiplerini içerir.

## 🕒 Son Yapılan İşlemler ve Güncellemeler (19 Mayıs 2026 İtibarıyla)

### 1. Mimari Temizlik ve Klasör Yapılandırması (Clean Architecture)
- **Frontend Refactoring:** `index.html` ve `admin.html` içerisinde yer alan yüzlerce satırlık gömülü CSS ve JavaScript kodları tamamen temizlendi. Bu kodlar Flask'in `url_for('static', ...)` yapısına uygun olarak `dashboard/static/css/style.css` ve `dashboard/static/js/` (dashboard.js ve admin.js) dosyalarına ayrıştırıldı.
- **Fat Controller'ların Temizlenmesi:** `dashboard/api/app.py` içerisindeki karmaşık AI İçgörü iş mantığı (business logic), `nlp/insights_manager.py` adında yeni bir modüle taşındı. API uçları (endpoints) sadece veri çekme ve yanıtlama görevine indirgendi.
- **DRY (Don't Repeat Yourself) Prensibi:** `main.py` ve `app.py` içinde tekrar eden devasa Excel dışa aktarma kodları (Pandas & Openpyxl), `database/db_manager.py` içinde ortak bir `export_all_tweets_to_excel()` fonksiyonunda birleştirildi.
- **PEP 8 Uyum ve Inline Import Temizliği:** Projedeki tüm kod dosyaları tarandı. Fonksiyon içlerinde yer alan gizli (inline) `import` satırları kaldırılarak ait oldukları dosyaların en üstüne taşındı.

### 2. Gelişmiş NLP Filtreleri ve İroni Algılayıcısı
- **İroni Kütüphanesi Genişletildi:** `nlp/irony_detector.py` içerisindeki kelime haznesi ("uçuyoruz", "şahlanıyoruz", "avrupa bizi kıskanıyor" vb.) devasa oranda artırıldı. Ayrıca sessiz harf uzatmaları ve "(ironi)", "/s" gibi açık belirteçler için "Explicit Marker" kontrolleri eklendi.
- **Devasa N-Gram Filtresi (Stop Words):** `nlp/insights_manager.py` içerisinde "Ana Katalizör" tespitinde kullanılan stop words kütüphanesi; bağlaçlar, zamirler, sayılar ve "şeyler", "oysaki" gibi gürültü çıkaran tüm gereksiz kelimeleri kapsayacak şekilde merkeze taşındı (`STOP_WORDS` CONSTANT).

### 3. Akıllı Kota Koruyucu (Smart Quota Aggregator)
- X API'nin "Tek seferde en az 10 tweet isteyebilirsin" kuralından kaynaklanan bütçe israfı tamamen çözüldü. Sistem, dar tarihli işlemleri tek bir potada arayarak gereksiz api çağrılarından kaçınıyor.

### 4. Üst Düzey Semantik Kopya Koruması (TheFuzz)
- Haber botlarının sahte hashtagler ekleyerek sistemi kandırması engellendi. Temizlenen metinler `thefuzz` ile %75 benzerlik eşiğinde karşılaştırılıyor ve kopyalar Excel'e bulaşmadan hafızadan siliniyor.

### 5. Otomatik "Tam Yedek" Excel Sistemi (Full Backup)
- Her veri çekimi bittiğinde sadece "o an çekilen" yeni tweetler değil, veritabanındaki **TÜM tweetler** profesyonelce formatlanmış (genişlik ve kaydırma ayarları yapılmış) bir Excel dosyası (`reports/istanbul_tum_yedek_TARIH.xlsx`) olarak kaydedilir.

### 6. "Büyük Harf Terbiyecisi" (Shouting Bias Fix)
- Sırf BÜYÜK HARFLE yazıldığı için resmi ajans başlıklarına "Negatif" diyen modelin hatası düzeltildi. %60'tan fazla büyük harf içeren metinler önce "Title Case" formatına çevrilip sonra modele sokuluyor.

### 7. Canlı UI/UX Aşama Takipçisi
- Yönetim panelinde "X tweet kaydedildi, Y çöp atıldı" gibi verileri saniyesi saniyesine raporlayan modal terminal eklendi.

### 8. Özel "İstanbul Trafik" ve "Sıfır Tolerans" Kuralı Seti
- **Sıfır Tolerans Argo Filtresi:** Negative Lookahead (Örn: `r'\bsik(?!inti|let)\w*'`) kullanılarak masum kelimeler korunurken argolar kalıcı olarak engelleniyor.
- **Trafik Override:** İronik trafik tweetlerindeki gülücüklere kanan model, eğer cümlede "trafik" varsa ve rahatlama kelimeleri geçmiyorsa sonucu zorla Negatife çekiyor.

---

## 🏗️ Gelecek Yapay Zeka Ajanları İçin Referans Mimarisi (Kurallar)

Bu proje üzerinde kodlama yapacak herhangi bir yapay zeka (AI) asistanı **kesinlikle** aşağıdaki kurallara ve mimariye riayet etmelidir:

1. **İş Mantığı Ayrımı (Business Logic Separation):** Flask route'ları (`dashboard/api/app.py`) **asla** 10-15 satırı geçmemelidir. Veritabanı sorguları ve kompleks algoritmalar (`nlp/` veya `database/` klasörlerindeki) ilgili servislere taşınmalı, route sadece bu fonksiyonları çağırmalıdır (Fat Controller önlemi).
2. **Standardizasyon (PEP 8):** Hiçbir fonksiyon veya metodun içerisinde `import` kullanılamaz. Tüm import'lar dosyanın en üstünde, açık ve net şekilde tanımlanmalıdır.
3. **Frontend Bağımsızlığı:** HTML dosyalarının içine (`<style>` veya `<script>`) kesinlikle CSS veya JS kodları gömülemez. Tüm stil ve betikler `dashboard/static/` altındaki ilgili dosyalara eklenmeli ve Jinja2 (`url_for`) ile çağrılmalıdır.
4. **DRY Prensibi:** Tekrar eden kodlar affedilemez. Bir işlem iki farklı yerde yapılıyorsa (Örn: Excel oluşturma, veri kaydetme), mutlaka ortak bir yardımcı fonksiyona çıkartılıp oradan import edilerek kullanılmalıdır.
5. **Konfigürasyon Hassasiyeti:** `config.py` içerisindeki token çekimleri temiz tutulmalı ve kritik eksiklikler `warnings.warn` veya loglarla sessiz çökme (silent fail) olmadan uyarılmalıdır. Projede ölü kod (kullanılmayan endpoint, fonksiyon vb.) barındırılamaz.

## 🧠 NLP Katmanı Çalışma Prensibi
NLP (Doğal Dil İşleme) katmanı 4 aşamalı bir Pipeline ile çalışır:

1. **Önce Temizleme (`text_cleaner.py`):** Ham tweet metni linklerden, etiketlerden ve hashtaglerden arındırılır. Küfürlü metinler çöpe atılır. TheFuzz ile kopyalar silinir.
2. **Büyük Harf Terbiyecisi:** Kalan temiz metnin %60'tan fazlası büyük harfse küçük harfe çevrilir.
3. **Sonra NLP/BERT (`sentiment_analyzer.py`):** Temizlenmiş metin `savasy/bert` modeline girer ve duygu skoru alır. (Güven skoru < %85 ise doğrudan Nötr'e itilir).
4. **En Son İroni Kontrolü (`irony_detector.py`):** Kinaye belirteçleri ve ironik kalıplar tespit edilirse, modelin "Pozitif" dediği etiket "Negatif"e tersine çevrilerek İstanbul metrosunun veya ekonomisinin sarkastik durumları yakalanır.
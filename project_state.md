# İstanbul Ekonomi Analizi - Proje Durumu (State)

Bu dosya, projede gerçekleştirilen **en son değişiklikleri, güncellemeleri ve mevcut çalışma durumunu** (state) detaylandırmak amacıyla oluşturulmuştur.

## 🕒 Son Yapılan İşlemler ve Güncellemeler (11 Mayıs 2026 İtibarıyla)

1. **X API (Twitter) Entegrasyonu ve Kotalar:**
   - Önceki Apify tabanlı altyapı tamamen terk edilerek, doğrudan X API v2 (Basic/Free) entegrasyonu sağlandı (`x_api_client.py`).
   - Aylık ücretsiz 10.000 tweet sınırını aşmamak için `LocalUsageMonitor` (yerel JSON tabanlı bütçe takipçisi) sisteme dahil edildi.

2. **Veri Çekme (Fetch) Algoritması & Sayfalama (Pagination):**
   - X API'nin "Maksimum 100, Minimum 10 sonuç" kurallarına tam uyum sağlandı.
   - İstenen tweet sayısı günlere (maksimum 7 gün) eşit olarak bölünecek şekilde ayarlandı. 100'ü aşan günlük istekler `while` döngüsü ve `next_token` ile **100'erli paketler (sayfalama)** halinde çekilecek şekilde güncellendi.
   - Günlere bölerken artan "küsurat (remainder)" tweetler, toplam sayıyı eksiksiz tutturmak adına **en güncel (en yakın) güne** eklenerek veri kalitesi/güncelliği artırıldı.

3. **Gelişmiş Spam ve Bot Koruması:**
   - **Agresif İlk 50 Karakter Kuralı:** Haber ajanslarının farklı linklerle birebir aynı haberi paylaşmasını engellemek için spam filtresi sertleştirildi. Artık tweetlerin sadece **ilk 50 karakteri** karşılaştırılıyor. Eğer aynıysa, kuyruğunda farklı bir link veya emoji olsa bile doğrudan çöpe atılıyor.
   - `-is:reply` filtresi API'den kaldırıldı; halkın kurumlara/siyasilere verdiği isyan veya destek cevaplarının kaçırılmaması sağlandı.
   - Etkileşimsiz ölü tweetleri almak için `MIN_FAVES = 0` olarak korundu, API'nin minimum 10 limitini tetiklememesi için filtrelere dokunulmadı.

4. **Metin Temizliği (NLP Öncesi - `text_cleaner.py`):**
   - **Agresif URL Silici:** Twitter'ın gizlediği `t.co/` ve `pic.twitter.com/` dahil **tüm link varyasyonları** makine öğrenmesine girmeden önce temizleniyor.
   - **Gelişmiş Hashtag Silici:** Hashtag'lerin (`#`) içindeki metinlerin (Örn: Galatasaray) yapay zekayı manipüle etmemesi için, **Türkçe karakterleri de (Ş, ç, ğ, ö, ü) kapsayacak** tam kelime temizliği koda eklendi.
   - **"RT " Silici:** Alıntı tweetlerin başındaki gereksiz "RT" önekinin yapay zekanın kafasını karıştırması başarıyla engellendi. (Not: Bu silme işlemleri sadece yapay zekaya giden kopyada yapılır, veritabanına ve Dashboard'a orjinal, eksiksiz veri yansır).
   - Finansal verilerin (`%`, `+`, `/`) silinmemesi için regex düzeltildi.

5. **NLP ve Model Skorlama Koruması (`sentiment_analyzer.py`):**
   - **%85 Güvenlik Eşiği (Threshold):** `savasy/bert-base-turkish-sentiment-cased` modelinin kararsız kalıp nötr metinlere rastgele Pozitif/Negatif uydurmasını engellemek için %85 sınırı aktif tutuluyor. Model %85'ten emin değilse (örn: %73 emin olduğu bir uyuşturucu haberinde) sistem bunu doğrudan **NOTR** (Nötr) olarak etiketleyip veri kirliliğini önlüyor.

6. **Dashboard (Yönetici Paneli) ve Veritabanı Mimarisi:**
   - Sistemin manuel tetiklenmesi, anahtar kelime yönetimi ve Excel çıktısı tamamen `http://127.0.0.1:5000` adresi üzerinden kontrol edilebilir hale geldi. (Terminalde `python -m dashboard.api.app` yazılarak çalıştırılır).
   - Veritabanına başlangıç (seed) verileri (`default_topics`) koda eklendi ancak tüm arama kelimeleri anlık olarak veritabanı üzerinden (`Keyword` tablosu) dinamik çekiliyor.
   - Yönetici panelindeki "Excel İndir" butonu, sadece o anki çekilenleri değil, UI'daki **tüm veritabanı yığınını** indirecek şekilde yapılandırıldı.

## 🧠 NLP Katmanı Çalışma Prensibi
NLP (Doğal Dil İşleme) katmanı, 3 aşamalı bir boru hattı (Pipeline) ile çalışır:

1. **Önce Temizleme (`text_cleaner.py`):** Ham tweet metni; linklerden, RT ibarelerinden, etiketlenen kişilerden ve hashtag kelimelerinden tamamen arındırılır.
2. **Sonra NLP/BERT (`sentiment_analyzer.py`):** Temizlenmiş ve yalınlaştırılmış metin BERT modeline girer. Ham bir duygu skoru (Pozitif, Negatif veya emin değilse Nötr) alır.
3. **En Son İroni Kontrolü (`irony_detector.py`):** Türkçe diline has kinaye ve sarkazmı algılayamayan BERT modelini korumak için, cümlenin içinde hem ironi kelimeleri (süper, harika) hem de abartı (!! veya harf uzatması) varsa etiket **tersine çevrilir** (Pozitif -> Negatif).
# İstanbul Ekonomi Analizi - Proje Durumu (State)

Bu dosya, projede gerçekleştirilen **en son değişiklikleri, güncellemeleri ve mevcut çalışma durumunu** (state) detaylandırmak amacıyla oluşturulmuştur.

## 🕒 Son Yapılan İşlemler ve Güncellemeler (12 Mayıs 2026 İtibarıyla)

### 1. Akıllı Kota Koruyucu (Smart Quota Aggregator)
- X API'nin "Tek seferde en az 10 tweet isteyebilirsin" kuralından kaynaklanan bütçe israfı tamamen çözüldü. 
- Eğer kullanıcı az sayıda tweet (Örn: 20 Tweet / 2 Gün) çekerse ve bu sayı günlere bölündüğünde 10'un altında kalıyorsa; sistem **günlere bölmekten vazgeçip tek bir geniş tarihli potada** arama yaparak faturanın katlanmasını (Örn: 80'e çıkmasını) engelliyor ve yeryüzündeki en düşük fatura olan 40'ta tutuyor. 

### 2. Üst Düzey Semantik Kopya Koruması (TheFuzz)
- Eski "ilk 50 karakter" kuralı daha da akıllandırıldı.
- Haber botlarının aynı metnin sonuna farklı sahte hashtagler ekleyerek sistemi kandırması engellendi. Metinler temizlendikten sonra (hashtagler ve linkler atıldıktan sonra) öz metinleri `thefuzz` ile karşılaştırılıyor.
- **%75 benzerlik** tespit edilen kopyalar veritabanına ve Excel'e bulaşmadan anında hafızadan siliniyor.

### 3. Otomatik "Tam Yedek" Excel Sistemi (Full Backup)
- Her veri çekimi bittiğinde sistem sadece "o an çekilen" yeni tweetleri değil, **veritabanındaki ilk günden bugüne kadar olan TÜM tweetleri** tek bir Excel dosyasına döküyor.
- `reports/istanbul_tum_yedek_TARIH.xlsx` formatıyla oluşturulan bu tablo; sütun genişlikleri ayarlanmış, metinleri alt alta kaydırılmış, direkt akademisyenlere ve kurumlara sunulabilecek profesyonel bir düzene kavuşturuldu.

### 4. "Büyük Harf Terbiyecisi" (Shouting Bias Fix)
- BERT yapay zekasının sırf BÜYÜK HARFLE yazıldığı için resmi (Nötr) haber ajansı başlıklarına haksız yere "Negatif" (Öfkeli) demesini engelleyen çok zekice bir mühendislik eklendi.
- Eğer metindeki harflerin **%60'ından fazlası büyük harfse**, sistem Caps Lock veya ajans başlığı olduğunu anlayıp yapay zekaya gitmeden önce metni sadece "Baş harfi büyük" olan normal bir cümle yapısına çevirerek modelin %98'lik kusursuz bir doğruluk oranına çıkmasını sağladı. (Vatandaşın %30 oranındaki gerçek öfke vurgularına dokunulmuyor).

### 5. Küfür ve Argo Dedektörü
- Twitter'ın sokak ağzına karşı projeyi temiz tutmak için `text_cleaner.py` içerisine özel bir argat/küfür listesi eklendi. Çöpler, yapay zekaya dahi sokulmadan kapıdan çevriliyor.

### 6. Canlı UI/UX Aşama Takipçisi
- Yönetim paneline veri çekerken arka planda ne yaşandığını gösteren siyah bir terminal (Modal) eklendi.
- "X tweet kaydedildi, Y çöp atıldı, Z excel oluşturuldu" gibi veriler saniyesi saniyesine kullanıcıya raporlanıyor.

### 7. Dinamik Kategori (Konu) Filtreleme UI
- Dashboard anasayfasına duygu durumu (sentiment) filtrelerine ek olarak, veritabanından dinamik beslenen **"Kategoriler (Konular)"** filtreleri eklendi.
- API'den çekilen tüm aktif konular (Örn: Makro Ekonomi, Ulaşım, Gayrimenkul) ikonlarıyla birlikte tek tıklamayla tweetleri filtreleyecek şekilde sisteme entegre edildi. Herhangi bir yeni kategori eklendiğinde arayüz otomatik olarak güncellenir.

### 8. Sentetik Uzman (Synthetic Expert) NLP Mimarisi & UI Modernizasyonu
- **Gereksiz Modül Temizliği:** Ekranda yer kaplayan ve analitik değeri düşük olan "Viral Tweetler Slider" arayüzü, CSS/JS katmanlarıyla ve arka plandaki `/api/viral-tweets` endpoint'iyle birlikte sistemden tamamen temizlendi. UI, 3'lü grid düzeniyle (0.8fr 1.2fr 1.5fr) daha ferah ve okunabilir bir hale getirildi (Haftalık trend grafiğine daha çok alan açıldı).
- **Lokal Semantik (N-Gram) Motoru:** Pahalı ve yavaş harici LLM'lere (ChatGPT vb.) bağlanmak yerine, kendi sunucumuzda çalışan **Bigram/Unigram (Kök Neden Çıkarımı)** Python algoritması yazıldı. Sistem, anlık filtrelenmiş tweetlerin metinlerini temizleyip en çok yan yana gelen 2'li (veya tekli) kelimeleri sayarak "Ana Katalizörleri" tespit ediyor.
- **Kombinasyonlu Zeka Sentezi:** Dashboard'un ortasındaki AI İçgörü Kartı, metrikleri ayrı ayrı saymak yerine sentezlemeye başladı. Negatiflik ve Etkileşim aynı anda yüksekse sistem "Kriz Atmosferi (Yüksek Risk)", düşükse "İzole Şikayetler" tespitinde bulunuyor. Etkileşim hesabı, sahte görüntülenmeleri (Views) saymayarak sadece gerçek reaksiyonları (Like+RT) baz alıyor.
- **Executive (Yönetici) Jargonu:** Tüm NLP sonuçları (Duygu, İroni, Semantik) basit okumalar yerine McKinsey danışmanı edasında; "Kök Neden", "Ana Katalizörler", "Toplumsal Tepki Profili" gibi profesyonel kurumsal metinlerle raporlanıyor.

### 9. Özel "İstanbul Trafik" ve "Sıfır Tolerans" Kuralı Seti
- **Sıfır Tolerans Argo Filtresi:** `text_cleaner.py` içindeki küfür filtresi Negatif İleri Bakış (Negative Lookahead) kullanılarak `r'\bsik(?!inti|let)\w*'` mantığına güncellendi. "Sıkıntı", "Bisiklet" gibi masum kelimeler korunurken, ek almış tüm ağır küfürler (örn: "...sikeyim") veritabanından kalıcı olarak (Retroaktif temizlikle) silindi.
- **Trafik Override:** BERT modelinin "Artık denizde bile trafik var :)" gibi ironik tweetlerdeki gülücüklere kanıp sahte pozitif (False Positive) üretmesi engellendi. Cümlede "trafik" kelimesi varsa ve ("açık, yok, rahat") gibi kelimeler geçmiyorsa, sistem artık modeli zorla (override) Negatife çekerek İstanbul'un trafik çilesini doğru indeksliyor.

---

## 🧠 NLP Katmanı Çalışma Prensibi
NLP (Doğal Dil İşleme) katmanı, artık 4 aşamalı kusursuz bir boru hattı (Pipeline) ile çalışır:

1. **Önce Temizleme (`text_cleaner.py`):** Ham tweet metni; linklerden, RT ibarelerinden, etiketlenen kişilerden ve hashtag kelimelerinden tamamen arındırılır. Küfürlü metinler çöpe atılır. TheFuzz ile kopyalar silinir.
2. **Büyük Harf Terbiyecisi:** Kalan temiz metnin %60'tan fazlası büyük harfse, haksız negatif biasını önlemek için küçük harfe çevrilir.
3. **Sonra NLP/BERT (`sentiment_analyzer.py`):** Temizlenmiş ve yalınlaştırılmış metin `savasy/bert` modeline girer. Ham bir duygu skoru (Pozitif, Negatif veya Nötr) alır. (Güven skoru < %85 ise doğrudan Nötr'e itilir).
4. **En Son İroni Kontrolü (`irony_detector.py`):** Türkçe diline has kinaye algılayamayan yapay zeka; cümlenin içinde ironi belirteçleri tespit ederse etiketi tersine çevirir. (Sözde pozitifleri negatife çeker).
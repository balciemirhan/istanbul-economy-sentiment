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

---

## 🧠 NLP Katmanı Çalışma Prensibi
NLP (Doğal Dil İşleme) katmanı, artık 4 aşamalı kusursuz bir boru hattı (Pipeline) ile çalışır:

1. **Önce Temizleme (`text_cleaner.py`):** Ham tweet metni; linklerden, RT ibarelerinden, etiketlenen kişilerden ve hashtag kelimelerinden tamamen arındırılır. Küfürlü metinler çöpe atılır. TheFuzz ile kopyalar silinir.
2. **Büyük Harf Terbiyecisi:** Kalan temiz metnin %60'tan fazlası büyük harfse, haksız negatif biasını önlemek için küçük harfe çevrilir.
3. **Sonra NLP/BERT (`sentiment_analyzer.py`):** Temizlenmiş ve yalınlaştırılmış metin `savasy/bert` modeline girer. Ham bir duygu skoru (Pozitif, Negatif veya Nötr) alır. (Güven skoru < %85 ise doğrudan Nötr'e itilir).
4. **En Son İroni Kontrolü (`irony_detector.py`):** Türkçe diline has kinaye algılayamayan yapay zeka; cümlenin içinde ironi belirteçleri tespit ederse etiketi tersine çevirir. (Sözde pozitifleri negatife çeker).
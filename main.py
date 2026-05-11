import logging
import os
import time
from database.db_manager import init_db, save_tweets_bulk
from api.tweet_fetcher import TweetFetcher
from nlp.sentiment_analyzer import SentimentAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_pipeline(max_tweets=100, days=7, status_callback=None):
    """
    Tüm analizi başlatan ana fonksiyon. Flask üzerinden çağrılabilmesi için modüler yapıldı.
    status_callback: Arayüze anlık durum bilgisi göndermek için çağrılan bir fonksiyon.
    """
    def update_status(status_msg):
        logger.info(status_msg)
        if status_callback:
            status_callback(status_msg)

    update_status("=== İstanbul Ekonomi Analizi Başlatılıyor ===")
    
    # 1. Veritabanını başlat
    update_status("Veritabanı kontrol ediliyor...")
    init_db()
    
    # 2. Modülleri yükle
    update_status("Sistem bileşenleri yükleniyor (BERT Modeli dahil)...")
    fetcher = TweetFetcher()
    analyzer = SentimentAnalyzer()
    
    # 3. Veri çekimi
    update_status(f"Adım 1: X API üzerinden en fazla {max_tweets} adet tweet çekiliyor...")
    
    tweets = fetcher.fetch_tweets(max_tweets=max_tweets, days=days)
    
    if not tweets:
        update_status("İşlenecek yeni tweet bulunamadı veya kotaya ulaşıldı.")
        return {"success": True, "saved": 0, "filtered": 0, "message": "Tweet bulunamadı."}

    # 4. Analiz ve Kayıt
    update_status("Adım 2: Duygu analizi ve metin temizliği yapılıyor...")
    
    from nlp.text_cleaner import clean_tweet_text
    from database.db_manager import get_recent_tweet_texts
    
    processed_tweets = []
    filtered_count = 0
    total_tweets = len(tweets)
    
    seen_texts = set() # Spam/Bot hesapların aynı metni kopyalamasını engellemek için
    
    # Veritabanındaki geçmiş tweetlerin metinlerini (son 'days' gün) alıp seen_texts'e ekle
    db_texts = get_recent_tweet_texts(days=days)
    for t_text in db_texts:
        cleaned_db = clean_tweet_text(t_text)
        if len(cleaned_db) >= 15:
            seen_texts.add(cleaned_db[:50])
            
    update_status(f"Geçmiş veritabanından {len(seen_texts)} benzersiz metin referansı kopyaları engellemek için hafızaya alındı.")
    
    for i, tweet in enumerate(tweets):
        # Yüzdelik ilerleme göstermek için callback (Opsiyonel ama hoş olur)
        if i % 10 == 0:
            update_status(f"Analiz ediliyor: {i}/{total_tweets} tamamlandı...")

        cleaned_text = clean_tweet_text(tweet['text'])
        
        # 1. Kısa veya anlamsız metinleri ele
        if len(cleaned_text) < 15:
            filtered_count += 1
            continue
            
        # 2. Benzer metne sahip olan bot/haber tweetlerini ele (Agresif Spam Koruması)
        # Tweetin ilk 50 karakteri aynıysa bunu kopyalanmış haber veya spam kabul edip eliyoruz
        text_prefix = cleaned_text[:50]
        if text_prefix in seen_texts:
            filtered_count += 1
            continue
            
        seen_texts.add(text_prefix)
            
        # Analiz
        nlp_result = analyzer.analyze(tweet['text'])
        tweet['sentiment'] = nlp_result['sentiment']
        tweet['score'] = nlp_result['score']
        tweet['is_ironic'] = nlp_result['is_ironic']
        
        # Listeye ekle
        processed_tweets.append(tweet)
        
    saved_count = 0
    if processed_tweets:
        update_status("Adım 3: Sonuçlar veritabanına toplu olarak (bulk) kaydediliyor...")
        save_tweets_bulk(processed_tweets)
        
        # Excel Raporu Çıktısı Al
        import pandas as pd
        from datetime import datetime
        os.makedirs("reports", exist_ok=True)
        excel_path = f"reports/istanbul_tweets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        df = pd.DataFrame(processed_tweets)
        df = df.drop_duplicates(subset=['tweet_id'], keep='first')
        df.to_excel(excel_path, index=False)
        update_status(f"Excel raporu oluşturuldu: {excel_path}")
        
    saved_count = len(processed_tweets)
        
    final_msg = f"Boru hattı tamamlandı. {saved_count} tweet kaydedildi, {filtered_count} kalitesiz tweet elendi."
    update_status(final_msg)
    update_status("=== Tüm İşlemler Başarıyla Bitti ===")
    
    return {"success": True, "saved": saved_count, "filtered": filtered_count, "message": final_msg}

def main():
    # Terminalden manuel çalıştırmak için
    run_pipeline(max_tweets=0) # Şu an için kapalı, test amaçlı 0

if __name__ == "__main__":
    main()

import logging
import os
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from database.db_manager import init_db, save_tweets_bulk
from api.tweet_fetcher import TweetFetcher
from nlp.sentiment_analyzer import SentimentAnalyzer

try:
    from thefuzz import fuzz
except ImportError:
    fuzz = None

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
    
    from nlp.text_cleaner import clean_tweet_text, contains_profanity
    from database.db_manager import get_recent_tweet_texts
    
    if fuzz is None:
        logger.error("thefuzz kütüphanesi eksik! 'pip install thefuzz python-Levenshtein' komutunu çalıştırın.")
    
    processed_tweets = []
    filtered_count = 0
    total_tweets = len(tweets)
    
    seen_texts = [] # Spam/Bot hesapların aynı metni kopyalamasını engellemek için listemiz
    
    # Veritabanındaki geçmiş tweetlerin metinlerini (son 'days' gün) alıp seen_texts'e ekle
    db_texts = get_recent_tweet_texts(days=days)
    for t_text in db_texts:
        cleaned_db = clean_tweet_text(t_text)
        if len(cleaned_db) >= 15:
            seen_texts.append(cleaned_db)
            
    update_status(f"Geçmiş veritabanından {len(seen_texts)} referans metin semantik kopya kontrolü (%75 eşik) için hafızaya alındı.")
    
    for i, tweet in enumerate(tweets):
        # Yüzdelik ilerleme göstermek için callback (Opsiyonel ama hoş olur)
        if i % 10 == 0:
            update_status(f"Analiz ediliyor: {i}/{total_tweets} tamamlandı...")

        cleaned_text = clean_tweet_text(tweet['text'])
        
        # 1. Kısa veya anlamsız metinleri ele
        if len(cleaned_text) < 15:
            filtered_count += 1
            continue
            
        # 2. Küfür ve kaba kelime filtresi (Orijinal ham metin üzerinden kontrol edilir)
        if contains_profanity(tweet['text']):
            filtered_count += 1
            continue
            
        # 3. Benzer metne sahip olan bot/haber tweetlerini ele (Semantik Kopya Koruması)
        # thefuzz.token_set_ratio ile %75 benzerlik varsa kopyalanmış haber veya spam kabul edip eliyoruz
        is_duplicate = False
        if fuzz is not None:
            for past_text in seen_texts:
                if fuzz.token_set_ratio(cleaned_text, past_text) >= 75:
                    is_duplicate = True
                    break
        else:
            # Fallback
            if any(cleaned_text[:50] == pt[:50] for pt in seen_texts):
                is_duplicate = True

        if is_duplicate:
            filtered_count += 1
            continue
            
        seen_texts.append(cleaned_text)
            
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
        saved_count = len(processed_tweets)
        
    # Her işlem bitiminde (yeni veri gelse de gelmese de) TÜM veritabanının güncel yedeğini Excel olarak reports/ klasörüne al.
    try:
        update_status("Adım 4: Veritabanının tam (full) yedeği Excel olarak oluşturuluyor...")
        import pandas as pd
        from datetime import datetime
        from database.db_manager import SessionLocal, Tweet
        
        db = SessionLocal()
        all_tweets = db.query(Tweet).all()
        db.close()
        
        if all_tweets:
            data = []
            for t in all_tweets:
                data.append({
                    "Tarih": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
                    "Kullanıcı": t.author_username,
                    "Tweet Metni": t.text,
                    "Duygu Durumu": t.sentiment.upper() if t.sentiment else "",
                    "Skor": round(t.score, 2) if t.score else 0,
                    "İroni mi?": "Evet" if t.is_ironic else "Hayır",
                    "Beğeni": t.likes,
                    "RT": t.retweets,
                    "Görüntülenme": t.views
                })
                
            os.makedirs("reports", exist_ok=True)
            excel_path = f"reports/istanbul_tum_yedek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df = pd.DataFrame(data)
            
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Tüm Yedek')
                worksheet = writer.sheets['Tüm Yedek']
                # Sütunları geniş ve okunaklı yap
                worksheet.column_dimensions['A'].width = 18
                worksheet.column_dimensions['B'].width = 18
                worksheet.column_dimensions['C'].width = 80
                worksheet.column_dimensions['D'].width = 15
                worksheet.column_dimensions['E'].width = 10
                worksheet.column_dimensions['F'].width = 12
                worksheet.column_dimensions['G'].width = 10
                worksheet.column_dimensions['H'].width = 10
                worksheet.column_dimensions['I'].width = 15
                from openpyxl.styles import Alignment
                for cell in worksheet['C']:
                    cell.alignment = Alignment(wrap_text=True)
                    
            update_status(f"Tam Excel yedeği başarıyla alındı (Toplam {len(all_tweets)} Tweet).")
    except Exception as e:
        logger.error(f"Excel yedeği alınırken hata: {e}")
        
    final_msg = f"Boru hattı tamamlandı. {saved_count} tweet kaydedildi, {filtered_count} kalitesiz tweet elendi."
    update_status(final_msg)
    update_status("=== Tüm İşlemler Başarıyla Bitti ===")
    
    return {"success": True, "saved": saved_count, "filtered": filtered_count, "message": final_msg}

def main():
    # Terminalden manuel çalıştırmak için
    run_pipeline(max_tweets=0) # Şu an için kapalı, test amaçlı 0

if __name__ == "__main__":
    main()

import os
import datetime
import logging
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database.models import Base, Tweet, Keyword
from config import DB_NAME

logger = logging.getLogger(__name__)

# SQLite Bağlantısı (Proje kök dizininde DB_NAME ile oluşturulacak)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = f"sqlite:///{os.path.join(BASE_DIR, f'{DB_NAME}.db')}"
engine = create_engine(db_path, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Veritabanı tablolarını oluşturur."""
    Base.metadata.create_all(bind=engine)
    seed_keywords_if_empty()

def save_tweet(tweet_data):
    """Tek bir tweeti veritabanına kaydeder."""
    db = SessionLocal()
    try:
        # Aynı tweet_id daha önce kaydedilmiş mi kontrol et
        exists = db.query(Tweet).filter(Tweet.tweet_id == str(tweet_data['tweet_id'])).first()
        if not exists:
            new_tweet = Tweet(
                tweet_id=str(tweet_data['tweet_id']),
                text=tweet_data['text'],
                author_username=tweet_data.get('author_username', ''),
                sentiment=tweet_data.get('sentiment', 'notr'),
                score=tweet_data.get('score', 0.0),
                is_ironic=tweet_data.get('is_ironic', False),
                likes=tweet_data.get('likes', 0),
                retweets=tweet_data.get('retweets', 0),
                views=tweet_data.get('views', 0),
                hashtags=tweet_data.get('hashtags', '')
            )
            db.add(new_tweet)
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Tweet kaydedilirken hata oluştu: {e}")
    finally:
        db.close()

def save_tweets_bulk(tweets_list):
    """Çoklu tweetleri tek bir seferde (bulk) veritabanına kaydeder."""
    db = SessionLocal()
    try:
        new_tweet_ids = [str(t['tweet_id']) for t in tweets_list]
        existing_tweets = db.query(Tweet.tweet_id).filter(Tweet.tweet_id.in_(new_tweet_ids)).all()
        existing_ids = {t[0] for t in existing_tweets}
        
        objects_to_save = []
        for tweet_data in tweets_list:
            t_id = str(tweet_data['tweet_id'])
            if t_id not in existing_ids:
                # String ISO tarihini datetime objesine çeviriyoruz (Eğer varsa)
                created_dt = datetime.datetime.utcnow()
                if tweet_data.get('created_at'):
                    try:
                        # Twitter'ın formatı: 2026-05-11T12:00:00.000Z
                        from dateutil import parser
                        created_dt = parser.isoparse(tweet_data['created_at']).replace(tzinfo=None)
                    except:
                        pass

                new_tweet = Tweet(
                    tweet_id=t_id,
                    text=tweet_data['text'],
                    author_username=tweet_data.get('author_username', ''),
                    created_at=created_dt,
                    sentiment=tweet_data.get('sentiment', 'notr'),
                    score=tweet_data.get('score', 0.0),
                    is_ironic=tweet_data.get('is_ironic', False),
                    likes=tweet_data.get('likes', 0),
                    retweets=tweet_data.get('retweets', 0),
                    views=tweet_data.get('views', 0),
                    hashtags=tweet_data.get('hashtags', '')
                )
                objects_to_save.append(new_tweet)
                existing_ids.add(t_id) # Aynı listede kopya varsa engellemek için
                
        if objects_to_save:
            db.bulk_save_objects(objects_to_save)
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Toplu tweet kaydedilirken hata oluştu: {e}")
    finally:
        db.close()

def get_dashboard_stats():
    """Dashboard'un ihtiyaç duyduğu temel istatistikleri çeker."""
    db = SessionLocal()
    try:
        total = db.query(Tweet).count()
        positive = db.query(Tweet).filter(Tweet.sentiment == 'pozitif').count()
        negative = db.query(Tweet).filter(Tweet.sentiment == 'negatif').count()
        neutral = db.query(Tweet).filter(Tweet.sentiment == 'notr').count()
        
        avg_score = db.query(func.avg(Tweet.score)).scalar() or 0.0
        
        return {
            "total": total,
            "positive": {"count": positive, "percentage": round((positive/total)*100, 1) if total > 0 else 0},
            "negative": {"count": negative, "percentage": round((negative/total)*100, 1) if total > 0 else 0},
            "neutral": {"count": neutral, "percentage": round((neutral/total)*100, 1) if total > 0 else 0},
            "avg_score": round(avg_score, 2)
        }
    finally:
        db.close()

def seed_keywords_if_empty():
    """Tablo boşsa yeni varsayılan kelimeleri ekler. Dinamik eklenenleri silmez."""
    db = SessionLocal()
    try:
        count = db.query(Keyword).count()
        if count == 0:
            default_topics = {
                "makro_ekonomi": ["enflasyon", "asgari ücret", "fatura", "pahalılık", "alım gücü", "zam geldi", "geçim derdi", "kredi kartı", "maaş", "gelir", "gıda fiyatı"],
                "ulasim_lojistik": ["mazot", "benzin", "akaryakıt zammı", "akbil", "iett zammı", "toplu taşıma ücreti", "taksi zammı", "köprü geçiş ücreti", "metrobüs zammı", "marmaray ücreti", "otobüs bileti"],
                "gayrimenkul_insaat": ["kira", "ev sahibi", "depozito", "emlak", "konut fiyatları", "aidat", "kiralık daire", "satılık ev", "ev fiyatı", "konut kredisi"],
                "ticaret_perakende": ["esnaf", "market fiyatları", "pazar arabası", "fahiş fiyat", "etiket fiyatı", "gramaj", "kasiyer", "mağaza fiyatları", "işyeri kirası", "ticaret odası"]
            }
            objects_to_save = []
            for category, words in default_topics.items():
                for word in words:
                    objects_to_save.append(Keyword(word=word, category=category))
            db.bulk_save_objects(objects_to_save)
            db.commit()
            logger.info("Varsayılan filtreleme kelimeleri veritabanına ilk kez eklendi.")
    except Exception as e:
        db.rollback()
        logger.error(f"Kelimeler güncellenirken hata oluştu: {e}")
    finally:
        db.close()

def get_active_keywords():
    """Tüm aktif kelimeleri liste olarak döner."""
    db = SessionLocal()
    try:
        keywords = db.query(Keyword).all()
        return [{"id": k.id, "word": k.word, "category": k.category} for k in keywords]
    finally:
        db.close()

def add_keyword(word, category="genel"):
    db = SessionLocal()
    try:
        existing = db.query(Keyword).filter(Keyword.word == word).first()
        if not existing:
            new_kw = Keyword(word=word, category=category)
            db.add(new_kw)
            db.commit()
            return {"success": True, "id": new_kw.id, "word": new_kw.word, "category": new_kw.category}
        return {"success": False, "error": "Bu kelime zaten var"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

def delete_keyword(kw_id):
    db = SessionLocal()
    try:
        kw = db.query(Keyword).filter(Keyword.id == kw_id).first()
        if kw:
            db.delete(kw)
            db.commit()
            return {"success": True}
        return {"success": False, "error": "Kelime bulunamadı"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

def get_recent_tweet_texts(days=7):
    """Son 'days' gün içindeki tweetlerin metinlerini döndürür. Spam/Kopya filtresi için kullanılır."""
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_tweets = db.query(Tweet.text).filter(Tweet.created_at >= cutoff_date).all()
        return [t[0] for t in recent_tweets if t[0]]
    except Exception as e:
        logger.error(f"Geçmiş tweet metinleri çekilirken hata: {e}")
        return []
    finally:
        db.close()


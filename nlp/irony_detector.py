import re

# İroni ve kinaye belirten Türkçe kelime öbekleri
IRONY_KEYWORDS = [
    "harika", "mükemmel", "süper", "muazzam", "şahane", "uçuyoruz", "şahlanıyoruz", 
    "kıskanıyor", "büyüyoruz", "asgari ücretli her gün antrikot yiyor", "tabi canım", 
    "aynen", "yersen", "kesin yaşanmıştır bu", "büyük oyun", "dış güçler", 
    "avrupa bizi kıskanıyor", "almanya bitmiş", "ekonomi çok iyi", "telefonunu çıkar", 
    "şükredin", "porsiyonları küçültün", "aa ne güzel", "maşallah", "nazar değmesin", 
    "vay be", "keşke", "yersen", "ironidir", "ironi", "sarkasm", "sarkastik"
]

# Performans için regex patternini bir kere derliyoruz
IRONY_PATTERN = re.compile(r'\b(' + '|'.join(map(re.escape, IRONY_KEYWORDS)) + r')\b')

def detect_irony(text):
    """
    Metinde ironi/kinaye olup olmadığını kural tabanlı olarak analiz eder.
    """
    text_lower = text.lower()
    
    # Explicit ironi işaretleri
    if any(marker in text_lower for marker in ["(ironi)", "/s", "(!)", "(?)"]):
        return True
    
    # Anahtar kelime var mı? (Derlenmiş regex kullanıyoruz)
    has_irony_pattern = bool(IRONY_PATTERN.search(text_lower))
    
    # Aşırı noktalama (!! veya ??) var mı?
    has_excessive_punctuation = text.count("!") > 1 or text.count("?") > 1
    
    # Harf uzatması (çoooooook, mükemmmeeeell, büyükkkk vs) var mı? 
    has_repeated_letters = bool(re.search(r'([a-zçğıöşü])\1{2,}', text_lower))
    
    # Eğer ironik kelimelerden biri varsa VE (aşırı noktalama veya harf uzatması) varsa
    if has_irony_pattern and (has_excessive_punctuation or has_repeated_letters):
        return True
        
    return False

def flip_sentiment(sentiment_label):
    """
    İroni tespit edildiğinde duygu etiketini tersine çevirir.
    """
    if sentiment_label == "pozitif":
        return "negatif"
    elif sentiment_label == "negatif":
        return "pozitif"
    return sentiment_label

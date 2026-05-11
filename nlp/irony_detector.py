import re

# İroni ve kinaye belirten Türkçe kelime öbekleri
IRONY_KEYWORDS = [
    "aa", "aha", "keşke", "ya", "vay", "maşallah", "ne güzel",
    "harika", "süper", "mükemmel", "aynen", "tabi canım", "yersen"
]

# Performans için regex patternini bir kere derliyoruz
IRONY_PATTERN = re.compile(r'\b(' + '|'.join(map(re.escape, IRONY_KEYWORDS)) + r')\b')

def detect_irony(text):
    """
    Metinde ironi/kinaye olup olmadığını kural tabanlı olarak analiz eder.
    """
    text_lower = text.lower()
    
    # Anahtar kelime var mı? (Derlenmiş regex kullanıyoruz)
    has_irony_pattern = bool(IRONY_PATTERN.search(text_lower))
    
    # Aşırı noktalama (!! veya ??) var mı?
    has_excessive_punctuation = text.count("!") > 1 or text.count("?") > 1
    
    # Harf uzatması (çoooooook, mükemmmeeeell) var mı?
    has_repeated_letters = any(c * 3 in text_lower for c in "aeıiouü")
    
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

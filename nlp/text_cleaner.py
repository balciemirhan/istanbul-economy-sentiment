import re

def clean_tweet_text(text):
    """
    BERT modeline girmeden önce metni gürültüden arındırır.
    """
    if not text:
        return ""
        
    # URL'leri kaldır (https, http, pic.twitter.com, t.co vb. her türlü varyasyon)
    text = re.sub(r'http[s]?://\S+|pic\.twitter\.com/\S+|t\.co/\S+', '', text)
    
    # Kullanıcı etiketlerini (@mention) kaldır
    text = re.sub(r'@\w+', '', text)
    
    # Hashtag'leri (#) kaldır (Türkçe karakterler dahil tüm etiketi ve kelimeyi siler ki gürültü/manipülasyon yapmasın)
    text = re.sub(r'#[\wçÇğĞıİöÖşŞüÜ]+', '', text)
    
    # Sadece harfler, rakamlar, temel noktalama işaretleri ve Türkçe karakterler kalsın (Emojileri uçarır)
    text = re.sub(r'[^\w\s\.,!\?\-\(\)\'":;çÇğĞıİöÖşŞüÜ]', '', text)
    
    # RT önekini kaldır
    text = re.sub(r'^RT[\s]+', '', text)
    
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def contains_profanity(text):
    """
    Tweetin içinde kaba, argo veya küfür içerikli kelimeler olup olmadığını kontrol eder.
    Büyük/küçük harf duyarsızdır.
    """
    if not text:
        return False
        
    text_lower = text.lower()
    
    # Twitter Türkiye'de en çok kullanılan kaba ve küfürlü kelimeler
    # \b kelime sınırlarını belirler ki 'sıkıntı' kelimesindeki 'sık' kısmı yanlışlıkla küfür algılanmasın.
    profanity_patterns = [
        r'\bamk\b', r'\bamq\b', r'\baq\b', r'\bmk\b', r'\ba\.q\b', r'\bo\.ç\b', r'\boç\b',
        r'siktir', r's\*ktir', r's\.ktir', r'\bsikik\b', r'\bsiker\b', r'\bsikey\b', r'\bsik\b', 
        r'orospu', r'\bpiç\b', r'\bpıc\b', r'\bgavat\b', r'\bibne\b', r'\byavşak\b', r'\byavsak\b',
        r'\bgöt\b', r'\bgot\b', r'\bamcık\b', r'\bamcik\b', r'şerefsiz', r'serefsiz', 
        r'pezevenk', r'kahpe', r'fahişe'
    ]
    
    for pattern in profanity_patterns:
        if re.search(pattern, text_lower):
            return True
            
    return False

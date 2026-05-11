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

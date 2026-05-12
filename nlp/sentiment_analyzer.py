from transformers import pipeline
import logging
from nlp.text_cleaner import clean_tweet_text
from nlp.irony_detector import detect_irony, flip_sentiment
from config import SENTIMENT_MODEL

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        logger.info(f"BERT modeli yükleniyor: {SENTIMENT_MODEL} (Bu işlem ilk seferde vakit alabilir)...")
        try:
            self.analyzer = pipeline("sentiment-analysis", model=SENTIMENT_MODEL)
            logger.info("BERT modeli başarıyla yüklendi.")
        except Exception as e:
            logger.error(f"Model yüklenirken hata oluştu: {e}")
            self.analyzer = None

    def map_label(self, label):
        """HuggingFace modelinden dönen etiketi standartlaştırır."""
        label = label.lower()
        if "positive" in label or "pozitif" in label or label == "label_1":
            return "pozitif"
        elif "negative" in label or "negatif" in label or label == "label_0":
            return "negatif"
        else:
            return "notr"

    def analyze(self, raw_text):
        """Metni alır, temizler, BERT'ten geçirir ve ironi kontrolü yapar."""
        if not self.analyzer:
            return {"sentiment": "notr", "score": 0.0, "is_ironic": False}
            
        # 1. Metni temizle
        clean_text = clean_tweet_text(raw_text)
        
        # Eğer temizlenmiş metin boşsa, nötr dön
        if not clean_text:
             return {"sentiment": "notr", "score": 0.0, "is_ironic": False}
             
        # BÜYÜK HARF TERBİYECİSİ (Shouting Bias Fix)
        # Metindeki harflerin (noktalama hariç) %60'ından fazlası büyük harfse,
        # model bunu öfke/bağırma sanmasın diye metni "Sadece baş harfi büyük" formata çevir.
        alpha_chars = [c for c in clean_text if c.isalpha()]
        if alpha_chars:
            upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
            if upper_ratio > 0.60:
                clean_text = clean_text.capitalize()
        
        # 2. BERT Analizi
        try:
            # truncation=True ile metin sınırlarını aşmayı engelliyoruz
            result = self.analyzer(clean_text, truncation=True, max_length=512)[0]
            base_sentiment = self.map_label(result['label'])
            score = result['score']
            
            # Model 2 sınıflı (Pozitif/Negatif) olduğu için kesinlik skoru düşükse (örn: < %85) bunu Nötr kabul ediyoruz
            if score < 0.85:
                base_sentiment = "notr"

        except Exception as e:
            logger.error(f"Analiz sırasında hata: {e}")
            return {"sentiment": "notr", "score": 0.0, "is_ironic": False}
            
        # 3. İroni Kontrolü
        is_ironic = detect_irony(raw_text)
        
        # 4. İroni varsa duygu etiketini tersine çevir
        final_sentiment = flip_sentiment(base_sentiment) if is_ironic else base_sentiment
        
        # 5. Kural Tabanlı Duygu Ezmesi (Override)
        # Sadece saf isyan/şikayet belirten kelimeler negatif yapılmalı.
        # "Zam" veya "asgari ücret" tek başına negatif değildir (Örn: "Asgari ücrete zam geldi çok sevindik").
        # Ancak içinde eylem/protesto kelimeleri geçiyorsa negatiftir.
        
        pure_negative_keywords = ["protesto", "eylem", "yürüyoruz", "yoksulluk", "açlık", "geçinemiyoruz", "pahalılık", "istifa", "isyan"]
        raw_lower = raw_text.lower()
        
        if final_sentiment == "pozitif":
            # Eğer saf isyan kelimelerinden biri geçiyorsa direkt negatif yap
            if any(kw in raw_lower for kw in pure_negative_keywords):
                final_sentiment = "negatif"
        
        return {
            "sentiment": final_sentiment,
            "score": round(score, 4),
            "is_ironic": is_ironic
        }

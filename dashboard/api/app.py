from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
import os
import threading
import pandas as pd
import io

from database.db_manager import SessionLocal, Tweet, Keyword, get_dashboard_stats, get_active_keywords, add_keyword, delete_keyword, init_db
from api.tweet_fetcher import LocalUsageMonitor, config
from sqlalchemy import or_

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

@app.after_request
def add_header(response):
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

FETCH_STATUS = {
    "is_running": False,
    "message": "Bekleniyor...",
    "logs": []
}

def update_fetch_status(msg):
    FETCH_STATUS["message"] = msg
    FETCH_STATUS["logs"].append(msg)
    if len(FETCH_STATUS["logs"]) > 10:
        FETCH_STATUS["logs"].pop(0)

def background_fetch_task(max_tweets, days):
    try:
        FETCH_STATUS["is_running"] = True
        FETCH_STATUS["logs"] = []
        update_fetch_status(f"Arka plan işlemi başlıyor ({max_tweets} hedef, {days} gün)...")
        
        # main_path eklemesine gerek yok çünkü root'tan çalıştırılacak
        from main import run_pipeline
        
        run_pipeline(max_tweets=max_tweets, days=days, status_callback=update_fetch_status)
        update_fetch_status("İşlem başarıyla tamamlandı.")
    except Exception as e:
        update_fetch_status(f"Hata oluştu: {str(e)}")
    finally:
        FETCH_STATUS["is_running"] = False

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Dashboard HTML dosyası bulunamadı: {e}", 500

@app.route('/admin')
def admin():
    try:
        return render_template('admin.html')
    except Exception as e:
        return f"Admin HTML dosyası bulunamadı: {e}", 500

@app.route('/api/stats')
def stats():
    try:
        stats_data = get_dashboard_stats()
        return jsonify(stats_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tweets')
def tweets():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    sentiment = request.args.get('sentiment', 'hepsi')
    topic = request.args.get('topic', 'hepsi')
    keyword = request.args.get('keyword', '')

    db = SessionLocal()
    try:
        query = db.query(Tweet)
        if sentiment != 'hepsi':
            query = query.filter(Tweet.sentiment == sentiment)
            
        if topic != 'hepsi':
            query = query.filter(Tweet.category == topic)
            
        if keyword:
            query = query.filter(Tweet.text.ilike(f"%{keyword}%"))

        total_count = query.count()
        offset = (page - 1) * limit
        
        recent_tweets = query.order_by(Tweet.created_at.desc()).offset(offset).limit(limit).all()
        
        tweets_list = []
        for t in recent_tweets:
            tweets_list.append({
                "id": t.tweet_id,
                "text": t.text,
                "user": f"@{t.author_username}",
                "date": t.created_at.strftime("%d %b"),
                "sentiment": t.sentiment,
                "score": t.score,
                "is_ironic": t.is_ironic
            })
            
        has_more = (offset + limit) < total_count
        
        return jsonify({
            "tweets": tweets_list,
            "has_more": has_more
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/viral-tweets')
def viral_tweets():
    sentiment = request.args.get('sentiment', 'hepsi')
    topic = request.args.get('topic', 'hepsi')
    
    db = SessionLocal()
    try:
        query = db.query(Tweet)
        if sentiment != 'hepsi':
            query = query.filter(Tweet.sentiment == sentiment)
        if topic != 'hepsi':
            query = query.filter(Tweet.category == topic)
            
        # En yüksek like + retweet toplamına göre sırala
        viral = query.order_by((Tweet.likes + Tweet.retweets).desc()).limit(5).all()
        
        result = []
        for t in viral:
            result.append({
                "id": t.tweet_id,
                "text": t.text,
                "user": f"@{t.author_username}",
                "date": t.created_at.strftime("%d %b"),
                "sentiment": t.sentiment,
                "likes": t.likes,
                "retweets": t.retweets,
                "total_engagement": t.likes + t.retweets
            })
            
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/api/ai-insights')
def ai_insights():
    sentiment = request.args.get('sentiment', 'hepsi')
    topic = request.args.get('topic', 'hepsi')
    
    db = SessionLocal()
    try:
        query = db.query(Tweet)
        if sentiment != 'hepsi':
            query = query.filter(Tweet.sentiment == sentiment)
        if topic != 'hepsi':
            query = query.filter(Tweet.category == topic)
            
        tweets = query.all()
        total_tweets = len(tweets)
        
        if total_tweets == 0:
            return jsonify([
                {"icon": "📭", "text": "Bu filtreye uygun yeterli veri bulunamadı."}
            ])
            
        # İstatistikleri hesapla
        pos_count = sum(1 for t in tweets if t.sentiment == 'pozitif')
        neg_count = sum(1 for t in tweets if t.sentiment == 'negatif')
        ironic_count = sum(1 for t in tweets if t.is_ironic)
        total_engagement = sum((t.likes or 0) + (t.retweets or 0) for t in tweets)
        
        pos_pct = (pos_count / total_tweets) * 100
        neg_pct = (neg_count / total_tweets) * 100
        irony_pct = (ironic_count / total_tweets) * 100
        
        insights = []
        
        # 1. ATMOSFER & RİSK SKORU (Sentez)
        if neg_pct > 55 and total_engagement > 1500:
            insights.append({
                "icon": "🚨", 
                "text": f"<b>Kriz Atmosferi (Yüksek Risk):</b> Hızla yayılan güçlü bir hoşnutsuzluk (%{neg_pct:.1f} Negatif, {total_engagement} Etkileşim). Konu ana akım (mainstream) tartışma eşiğini aşmış durumda."
            })
        elif neg_pct > 55:
            insights.append({
                "icon": "⚠️", 
                "text": f"<b>İzole Şikayetler (Bölgesel Hoşnutsuzluk):</b> Güçlü bir negatiflik eğilimi var (%{neg_pct:.1f}), ancak etkileşim hacmi ({total_engagement}) henüz geniş kitlelere sıçramadığını gösteriyor."
            })
        elif pos_pct > 55 and total_engagement > 1500:
            insights.append({
                "icon": "⭐", 
                "text": f"<b>Güçlü Pozitif Gündem:</b> Toplum genelinde net bir memnuniyet (%{pos_pct:.1f} Pozitif) ve yüksek katılım (Viral yayılım) gözlemleniyor."
            })
        elif pos_pct > 55:
            insights.append({
                "icon": "📈", 
                "text": f"<b>Ilımlı Memnuniyet:</b> Konu etrafında destekleyici ve pozitif (%{pos_pct:.1f}) bir hava hakim, stabil bir etkileşim mevcut."
            })
        else:
            if total_engagement > 1500:
                insights.append({
                    "icon": "⚖️", 
                    "text": f"<b>Yüksek Kutuplaşma:</b> Kitleler ikiye bölünmüş durumda. Yoğun bir etkileşim savaşı ({total_engagement}) ve duygu karmaşası var."
                })
            else:
                insights.append({
                    "icon": "📊", 
                    "text": f"<b>Stabil/Nötr Seyir:</b> Konuda radikal bir duygu baskınlığı veya viral bir sıçrama tespit edilmedi."
                })
        # 2. LOCAL NLP (N-GRAM) MOTORU (Kök Nedenler)
        stop_words = set([
            "bir", "ve", "bu", "ile", "de", "da", "için", "gibi", "çok", "istanbul", 
            "var", "yok", "kadar", "olan", "olarak", "daha", "en", "ki", "mi", "mı", 
            "mu", "mü", "ne", "niye", "ama", "fakat", "lakin", "ise", "diye", "ben", 
            "sen", "o", "biz", "siz", "onlar", "bana", "sana", "onu", "bunu", "şunu", 
            "her", "hiç", "sonra", "önce", "hangi", "nasıl", "neden", "niçin", "şimdi",
            "şu", "öyle", "göre", "kendi", "bile", "zaten", "başka", "tüm", "hep"
        ])
        
        import re
        from collections import Counter
        
        bigram_counts = Counter()
        unigram_counts = Counter()
        for t in tweets:
            text = str(t.text).replace('İ', 'i').replace('I', 'ı').lower()
            text = re.sub(r'http[s]?://\S+|pic\.twitter\.com/\S+|t\.co/\S+', '', text)
            text = re.sub(r'@\w+', '', text)
            words = [w for w in re.findall(r'[a-zçğıöşü]+', text) if len(w) > 2 and w not in stop_words]
            
            for w in words:
                unigram_counts[w] += 1
                
            if len(words) >= 2:
                for i in range(len(words)-1):
                    bigram = f"{words[i]} {words[i+1]}"
                    bigram_counts[bigram] += 1
                    
        top_bigrams = bigram_counts.most_common(2)
        if len(top_bigrams) == 2 and top_bigrams[0][1] > 1:
            bg1 = top_bigrams[0][0].title()
            bg2 = top_bigrams[1][0].title()
            insights.append({
                "icon": "🧬",
                "text": f"<b>Ana Katalizörler (Kök Neden):</b> Semantik analiz motorumuz, tepkilerin merkez üssünde spesifik olarak <b>'{bg1}'</b> ve <b>'{bg2}'</b> konularının yattığını tespit etti."
            })
        elif len(top_bigrams) > 0 and top_bigrams[0][1] > 1:
            bg1 = top_bigrams[0][0].title()
            insights.append({
                "icon": "🧬",
                "text": f"<b>Baskın Katalizör (Kök Neden):</b> Tartışmaları domine eden spesifik odak noktası <b>'{bg1}'</b> olarak ölçümlenmiştir."
            })
        else:
            top_unigrams = unigram_counts.most_common(2)
            if len(top_unigrams) == 2:
                ug1 = top_unigrams[0][0].title()
                ug2 = top_unigrams[1][0].title()
                insights.append({
                    "icon": "🧬",
                    "text": f"<b>Anahtar Konu Dağılımı:</b> Veri mimarimiz, mevcut tartışma havuzunda öne çıkan temaların <b>'{ug1}'</b> ve <b>'{ug2}'</b> olduğunu gösteriyor."
                })
            elif len(top_unigrams) == 1:
                ug1 = top_unigrams[0][0].title()
                insights.append({
                    "icon": "🧬",
                    "text": f"<b>Tekil Odak Noktası:</b> Sistemdeki dar veri setinde tespit edilen yegane kavramsal odak: <b>'{ug1}'</b>."
                })
            else:
                insights.append({
                    "icon": "🧬",
                    "text": "<b>Veri Yetersizliği:</b> Havuz, spesifik bir semantik örüntü veya kök neden çıkarılamayacak kadar dağınık."
                })

        # 3. DAVRANIŞSAL PROFİL
        if irony_pct > 10:
            insights.append({
                "icon": "🎭", 
                "text": f"<b>Toplumsal Tepki Profili:</b> Kitle reaksiyonlarını doğrudan yüzleşmek yerine, yoğun düzeyde (<b>%{irony_pct:.1f}</b>) alaycı ve sarkastik bir dille ifade etmeyi seçiyor."
            })
        elif irony_pct > 4:
            insights.append({
                "icon": "🤔", 
                "text": f"<b>Toplumsal Tepki Profili:</b> İfadelerde yer yer (<b>%{irony_pct:.1f}</b>) ironik bir ton kullanılsa da, iletişim genel olarak net."
            })
        else:
            insights.append({
                "icon": "🛡️", 
                "text": f"<b>Toplumsal Tepki Profili:</b> İroni oranı çok düşük. Kitle, öfkesini veya memnuniyetini hiçbir mecaza saklamadan, sert ve doğrudan bir yüzleşme diliyle dışa vuruyor."
            })
        return jsonify(insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

# --- ADMIN ENDPOINTS ---

@app.route('/api/keywords', methods=['GET'])
def get_keywords():
    return jsonify(get_active_keywords())

@app.route('/api/keywords', methods=['POST'])
def post_keyword():
    data = request.json
    word = data.get('word')
    category = data.get('category', 'genel')
    if not word:
        return jsonify({"error": "Kelime boş olamaz"}), 400
    res = add_keyword(word.lower(), category)
    if res.get("success"):
        return jsonify(res)
    return jsonify(res), 400

@app.route('/api/keywords/<int:kw_id>', methods=['DELETE'])
def del_keyword(kw_id):
    res = delete_keyword(kw_id)
    if res.get("success"):
        return jsonify(res)
    return jsonify(res), 400

@app.route('/api/usage', methods=['GET'])
def get_usage():
    monitor = LocalUsageMonitor()
    usage = monitor.get_current_month_usage()
    limit = config.MONTHLY_TWEET_BUDGET
    return jsonify({
        "used": usage,
        "limit": limit,
        "percentage": round((usage / limit) * 100, 1) if limit > 0 else 0
    })

@app.route('/api/fetch-data', methods=['POST'])
def fetch_data():
    if FETCH_STATUS["is_running"]:
        return jsonify({"error": "İşlem zaten devam ediyor"}), 400
        
    data = request.json or {}
    max_tweets = int(data.get('max_tweets', 100))
    days = int(data.get('days', 7))
    
    # X API Basic kısıtlamaları
    if days > 7: days = 7
    if days < 1: days = 1
    
    thread = threading.Thread(target=background_fetch_task, args=(max_tweets, days))
    thread.daemon = True
    thread.start()
    return jsonify({"success": True, "message": "Arka plan işlemi başlatıldı."})

@app.route('/api/fetch-status', methods=['GET'])
def fetch_status():
    return jsonify(FETCH_STATUS)

@app.route('/api/export', methods=['GET'])
def export_excel():
    db = SessionLocal()
    try:
        tweets = db.query(Tweet).all()
        data = []
        for t in tweets:
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
            
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Tum Tweetler')
            worksheet = writer.sheets['Tum Tweetler']
            
            # Sütun genişliklerini ayarla (sıkış bıkış olmaması için)
            worksheet.column_dimensions['A'].width = 18 # Tarih
            worksheet.column_dimensions['B'].width = 18 # Kullanıcı
            worksheet.column_dimensions['C'].width = 80 # Tweet Metni
            worksheet.column_dimensions['D'].width = 15 # Duygu
            worksheet.column_dimensions['E'].width = 10 # Skor
            worksheet.column_dimensions['F'].width = 12 # İroni
            worksheet.column_dimensions['G'].width = 10 # Beğeni
            worksheet.column_dimensions['H'].width = 10 # RT
            worksheet.column_dimensions['I'].width = 15 # Görüntülenme
            
            # Metni kaydır (Wrap text)
            from openpyxl.styles import Alignment
            for cell in worksheet['C']:
                cell.alignment = Alignment(wrap_text=True)

        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name="istanbul_ekonomi_tum_veriler.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return f"Excel oluşturulurken hata: {e}", 500
    finally:
        db.close()

if __name__ == '__main__':
    # Flask sunucusu başlatılmadan önce veritabanı tablolarını (Keyword vs.) kontrol et ve eksikse yarat
    init_db()
    
    print("Dashboard baslatiliyor... Tarayicinizda http://127.0.0.1:5000 adresine gidin.")
    app.run(debug=True, port=5000)

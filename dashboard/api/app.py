from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
import os
import threading
import pandas as pd
import io

from database.db_manager import SessionLocal, Tweet, get_dashboard_stats, get_active_keywords, add_keyword, delete_keyword, init_db
from api.tweet_fetcher import LocalUsageMonitor

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

    db = SessionLocal()
    try:
        query = db.query(Tweet)
        if sentiment != 'hepsi':
            query = query.filter(Tweet.sentiment == sentiment)
            
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
    return jsonify({
        "used": usage,
        "limit": 10000,
        "percentage": round((usage / 10000) * 100, 1)
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

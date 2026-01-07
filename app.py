import os, sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = 'bbk_pajet_secret_99'
socketio = SocketIO(app, cors_allowed_origins="*")

# Veritabanı Yolu
DB_PATH = '/tmp/bbk_final_v1.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Tabloları İlk Kez Oluştur
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS kuryeler 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, tel TEXT, durum TEXT DEFAULT 'Aktif', bakiye REAL DEFAULT 0)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS gonderiler 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, adres_al TEXT, adres_ver TEXT, fiyat REAL, durum TEXT DEFAULT 'Havuzda', kurye_id INTEGER)''')

@app.route('/') # Yönetim Paneli
def index():
    with get_db() as conn:
        kuryeler = conn.execute('SELECT * FROM kuryeler').fetchall()
    return render_template('index.html', kuryeler=kuryeler)

@app.route('/musteri', methods=['GET', 'POST'])
def musteri():
    if request.method == 'POST':
        al = request.form.get('adres_al')
        ver = request.form.get('adres_ver')
        fiyat = request.form.get('fiyat')
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO gonderiler (adres_al, adres_ver, fiyat) VALUES (?, ?, ?)', (al, ver, fiyat))
            conn.commit()
            is_id = cursor.lastrowid
        
        # TÜM KURYELERE DÜT DÜT GÖNDER
        socketio.emit('yeni_paket_dustu', {'id': is_id, 'adres_al': al, 'adres_ver': ver, 'fiyat': fiyat})
        return "<h1>Gönderi Havuza Atıldı!</h1><script>setTimeout(()=> window.location.href='/musteri', 2000);</script>"
    return render_template('musteri.html')

@app.route('/kurye_panel')
def kurye_panel():
    # Test kolaylığı için otomatik kurye girişi (Normalde login istenir)
    session['kurye_id'] = 1 
    with get_db() as conn:
        havuz = conn.execute('SELECT * FROM gonderiler WHERE durum = "Havuzda"').fetchall()
    return render_template('kurye_ekrani.html', havuz=havuz)

@app.route('/is_al/<int:id>', methods=['POST'])
def is_al(id):
    kurye_id = session.get('kurye_id')
    with get_db() as conn:
        is_durumu = conn.execute('SELECT durum FROM gonderiler WHERE id = ?', (id,)).fetchone()
        if is_durumu and is_durumu['durum'] == 'Havuzda':
            conn.execute('UPDATE gonderiler SET durum = "Aktif", kurye_id = ? WHERE id = ?', (kurye_id, id))
            conn.commit()
            # DİĞER KURYELERDEN SİL
            socketio.emit('is_sil_sinyali', {'id': id})
            return jsonify({'status': 'success', 'message': 'İş sizin oldu!'})
    return jsonify({'status': 'error', 'message': 'İş çoktan kapıldı!'}), 400

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)

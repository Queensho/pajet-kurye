import os, sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = 'pajet_anahtar_bbk'
socketio = SocketIO(app, cors_allowed_origins="*")

DB_PATH = '/tmp/pajet_v10.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanı ve tabloları oluştur
with get_db() as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS gonderiler (id INTEGER PRIMARY KEY AUTOINCREMENT, adres_al TEXT, adres_ver TEXT, fiyat REAL, durum TEXT DEFAULT "Havuzda", kurye_id INTEGER)')
    conn.execute('CREATE TABLE IF NOT EXISTS kuryeler (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, tel TEXT)')

@app.route('/')
def index():
    # Ana sayfaya girince direkt kurye paneline yönlendir
    return redirect(url_for('kurye_panel'))

@app.route('/kurye_panel')
def kurye_panel():
    session['kurye_id'] = 1 # Şimdilik herkesi 1 nolu kurye sayıyoruz
    with get_db() as conn:
        havuz = conn.execute('SELECT * FROM gonderiler WHERE durum = "Havuzda"').fetchall()
    return render_template('kurye_ekrani.html', havuz=havuz)

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
        
        socketio.emit('yeni_paket_dustu', {'id': is_id, 'adres_al': al, 'adres_ver': ver, 'fiyat': fiyat})
        return "<h1>İş Gönderildi!</h1><script>setTimeout(()=> window.location.href='/musteri', 2000);</script>"
    return render_template('musteri.html')

@app.route('/is_al/<int:id>', methods=['POST'])
def is_al(id):
    kurye_id = session.get('kurye_id')
    with get_db() as conn:
        check = conn.execute('SELECT durum FROM gonderiler WHERE id = ?', (id,)).fetchone()
        if check and check['durum'] == 'Havuzda':
            conn.execute('UPDATE gonderiler SET durum = "Aktif", kurye_id = ? WHERE id = ?', (kurye_id, id))
            conn.commit()
            socketio.emit('is_sil_sinyali', {'id': id})
            return jsonify({'status': 'success', 'message': 'İş senin!'})
    return jsonify({'status': 'error', 'message': 'Maalesef başkası kaptı.'}), 400

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

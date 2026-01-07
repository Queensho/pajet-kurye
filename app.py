import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'bbk_clone_secure_key'
DB_PATH = '/tmp/bbk_v1.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# BBK Veritabanı Şeması
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS kuryeler 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, tel TEXT, 
         durum TEXT DEFAULT 'Beklemede', bakiye REAL DEFAULT 0, puan REAL DEFAULT 5.0)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS gonderiler 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, tip TEXT, adres_al TEXT, adres_ver TEXT, 
         fiyat REAL, durum TEXT DEFAULT 'Havuzda', kurye_id INTEGER)''')

@app.route('/kurye_panel')
def kurye_panel():
    if 'kurye_id' not in session: return redirect('/kurye_giris')
    with get_db() as conn:
        kurye = conn.execute('SELECT * FROM kuryeler WHERE id = ?', (session['kurye_id'],)).fetchone()
        havuz = conn.execute('SELECT * FROM gonderiler WHERE durum = "Havuzda"').fetchall()
    return render_template('kurye_ekrani.html', kurye=kurye, havuz=havuz)

# app.py dosyasının içine yapıştırılacak bölüm:

@app.route('/is_al/<int:id>', methods=['POST'])
def is_al(id):
    # 1. Giriş yapan kuryeyi kontrol et
    kurye_id = session.get('kurye_id')
    if not kurye_id:
        return jsonify({'status': 'error', 'message': 'Lütfen önce giriş yapın'}), 401

    with get_db() as conn:
        # 2. İşin hala havuzda olup olmadığını (başkası kapmış mı) kontrol et
        is_durumu = conn.execute('SELECT durum FROM gonderiler WHERE id = ?', (id,)).fetchone()
        
        if is_durumu and is_durumu['durum'] == 'Havuzda':
            # 3. İşi bu kuryeye ata ve durumu güncelle
            conn.execute('UPDATE gonderiler SET durum = "Aktif", kurye_id = ? WHERE id = ?', (kurye_id, id))
            conn.commit()

            # 4. KRİTİK NOKTA: Diğer kuryelerin ekranından silmek için sinyal gönder
            socketio.emit('is_sil_sinyali', {'id': id})
            
            return jsonify({'status': 'success', 'message': 'İş başarıyla kapıldı!'})
        else:
            # İş zaten başkası tarafından alınmışsa hata döndür
            return jsonify({'status': 'error', 'message': 'Geç kaldınız, bu iş çoktan kapıldı!'}), 400

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

@app.route('/is_al/<int:id>')
def is_al(id):
    if 'kurye_id' in session:
        with get_db() as conn:
            # İşi kapma mantığı (Race Condition kontrolü)
            conn.execute('UPDATE gonderiler SET durum = "Aktif", kurye_id = ? WHERE id = ? AND durum = "Havuzda"', 
                         (session['kurye_id'], id))
            conn.commit()
    return redirect('/kurye_panel')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Render'da veritabanının düzgün çalışması için geçici klasör kullanıyoruz
DB_PATH = '/tmp/kurye_sistemi.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kuryeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim TEXT NOT NULL,
            tel TEXT NOT NULL,
            plaka TEXT NOT NULL,
            durum TEXT DEFAULT 'Onay Bekliyor'
        )
    ''')
    conn.commit()
    conn.close()

# Uygulama başladığında tabloyu oluştur
init_db()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    kuryeler = conn.execute('SELECT * FROM kuryeler').fetchall()
    conn.close()
    return render_template('index.html', kuryeler=kuryeler)

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        isim = request.form.get('isim')
        tel = request.form.get('tel')
        plaka = request.form.get('plaka')
        
        if isim and tel and plaka:
            conn = sqlite3.connect(DB_PATH)
            conn.execute('INSERT INTO kuryeler (isim, tel, plaka) VALUES (?, ?, ?)', 
                         (isim, tel, plaka))
            conn.commit()
            conn.close()
            return "<h1>Kayıt Başarılı!</h1><p>Yönetici paneline yönlendiriliyorsunuz...</p><script>setTimeout(function(){window.location.href='/';}, 3000);</script>"
        return "Lütfen tüm alanları doldurun!", 400
        
    return render_template('kayit.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

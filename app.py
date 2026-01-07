import os
from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)
# Render'da geçici veritabanı alanı
DB_PATH = '/tmp/operasyon.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanı tablosunu otomatik hazırlama
conn = get_db()
conn.execute('CREATE TABLE IF NOT EXISTS kuryeler (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, tel TEXT, plaka TEXT, durum TEXT DEFAULT "onay_bekliyor")')
conn.commit()
conn.close()

@app.route('/')
def index():
    conn = get_db()
    kuryeler = conn.execute('SELECT * FROM kuryeler').fetchall()
    conn.close()
    return render_template('index.html', kuryeler=kuryeler)

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        isim = request.form.get('isim')
        tel = request.form.get('tel')
        plaka = request.form.get('plaka')
        conn = get_db()
        conn.execute('INSERT INTO kuryeler (isim, tel, plaka) VALUES (?, ?, ?)', (isim, tel, plaka))
        conn.commit()
        conn.close()
        return "✅ Kayıt Alındı! Yönetici onayı bekleyin."
    return render_template('kayit.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

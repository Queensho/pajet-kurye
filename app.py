import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_PATH = '/tmp/pajet_v3.db' # Yeni bir db ismi vererek hata riskini sıfırlıyoruz

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanını ve gerekli tüm sütunları oluştur
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS kuryeler 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
         isim TEXT, tel TEXT, plaka TEXT, 
         durum TEXT DEFAULT 'Onay Bekliyor', 
         lat REAL DEFAULT 41.0082, 
         lng REAL DEFAULT 28.9784, 
         paket_sayisi INTEGER DEFAULT 0)''')

@app.route('/')
def index():
    with get_db() as conn:
        kuryeler = conn.execute('SELECT * FROM kuryeler').fetchall()
    return render_template('index.html', kuryeler=kuryeler)

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        with get_db() as conn:
            conn.execute('INSERT INTO kuryeler (isim, tel, plaka) VALUES (?, ?, ?)', 
                         (request.form['isim'], request.form['tel'], request.form['plaka']))
        return "<h1>Kayıt Başarılı!</h1><script>setTimeout(()=> window.location.href='/', 2000);</script>"
    return render_template('kayit.html')

@app.route('/islem/<int:id>', methods=['POST'])
def islem(id):
    aksiyon = request.form.get('aksiyon')
    with get_db() as conn:
        if aksiyon == 'onayla':
            conn.execute('UPDATE kuryeler SET durum = "Aktif" WHERE id = ?', (id,))
        elif aksiyon == 'sil':
            conn.execute('DELETE FROM kuryeler WHERE id = ?', (id,))
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

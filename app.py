import os, sqlite3
from flask import Flask, render_template, request, jsonify, redirect

app = Flask(__name__)
DB_PATH = '/tmp/kurye_sistemi.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanını yeni sütunlarla (lat, lng, paket) güncelleme
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS kuryeler 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, tel TEXT, plaka TEXT, 
         durum TEXT DEFAULT "Onay Bekliyor", lat REAL, lng REAL, paket_sayisi INTEGER DEFAULT 0)''')

@app.route('/')
def index():
    with get_db() as conn:
        kuryeler = conn.execute('SELECT * FROM kuryeler').fetchall()
    return render_template('index.html', kuryeler=kuryeler)

# Kurye uygulamasından gelen canlı konum ve paket verisi
@app.route('/update_data', methods=['POST'])
def update_data():
    data = request.json
    with get_db() as conn:
        conn.execute('UPDATE kuryeler SET lat = ?, lng = ?, paket_sayisi = ? WHERE id = ?',
                     (data['lat'], data['lng'], data['paket'], data['id']))
        conn.commit()
    return jsonify({"status": "success"})

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        with get_db() as conn:
            conn.execute('INSERT INTO kuryeler (isim, tel, plaka) VALUES (?, ?, ?)', 
                         (request.form['isim'], request.form['tel'], request.form['plaka']))
        return "<h1>Kayıt Alındı!</h1><script>setTimeout(()=> window.location.href='/', 2000);</script>"
    return render_template('kayit.html')

@app.route('/islem/<int:id>', methods=['POST'])
def islem(id):
    aksiyon = request.form.get('aksiyon')
    with get_db() as conn:
        if aksiyon == 'onayla':
            conn.execute('UPDATE kuryeler SET durum = "Aktif" WHERE id = ?', (id,))
        elif aksiyon == 'sil':
            conn.execute('DELETE FROM kuryeler WHERE id = ?', (id,))
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

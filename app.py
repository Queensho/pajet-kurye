import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)
DB_PATH = '/tmp/pajet_v4.db' # Veritabanı çakışmasını önlemek için v4 yaptık

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Tabloları oluştur (Kuryeler ve Gönderiler)
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS kuryeler 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, tel TEXT, plaka TEXT, durum TEXT DEFAULT 'Onay Bekliyor', lat REAL, lng REAL, paket_sayisi INTEGER DEFAULT 0)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS gonderiler 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, gonderen_tel TEXT, alici_adres TEXT, gidilecek_yer TEXT, tel TEXT, fiyat REAL, durum TEXT DEFAULT 'Havuzda')''')

@app.route('/') # Yönetim Paneli
def index():
    with get_db() as conn:
        kuryeler = conn.execute('SELECT * FROM kuryeler').fetchall()
        gonderiler = conn.execute('SELECT * FROM gonderiler WHERE durum="Havuzda"').fetchall()
    return render_template('index.html', kuryeler=kuryeler, gonderiler=gonderiler)

@app.route('/musteri', methods=['GET', 'POST']) # Müşteri Gönderi Ekranı
def musteri():
    if request.method == 'POST':
        with get_db() as conn:
            conn.execute('INSERT INTO gonderiler (gonderen_tel, alici_adres, gidilecek_yer, tel, fiyat) VALUES (?, ?, ?, ?, ?)',
                         (request.form['gonderen_tel'], request.form['alici_adres'], request.form['gidilecek_yer'], request.form['tel'], request.form['fiyat']))
        return "<h1>Gönderi Havuza Atıldı!</h1><script>setTimeout(()=> window.location.href='/musteri', 2000);</script>"
    return render_template('musteri.html')

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        with get_db() as conn:
            conn.execute('INSERT INTO kuryeler (isim, tel, plaka) VALUES (?, ?, ?)', (request.form['isim'], request.form['tel'], request.form['plaka']))
        return "<h1>Kayıt Alındı!</h1><script>setTimeout(()=> window.location.href='/', 2000);</script>"
    return render_template('kayit.html')

@app.route('/islem/<int:id>', methods=['POST'])
def islem(id):
    aksiyon = request.form.get('aksiyon')
    with get_db() as conn:
        if aksiyon == 'onayla': conn.execute('UPDATE kuryeler SET durum = "Aktif" WHERE id = ?', (id,))
        elif aksiyon == 'sil': conn.execute('DELETE FROM kuryeler WHERE id = ?', (id,))
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

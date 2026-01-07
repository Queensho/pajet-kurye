import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'pajet_ozel_anahtar'
DB_PATH = '/tmp/pajet_v6.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

with get_db() as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS kuryeler (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, tel TEXT, plaka TEXT, durum TEXT DEFAULT "Onay Bekliyor", paket_sayisi INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS gonderiler (id INTEGER PRIMARY KEY AUTOINCREMENT, alici_adres TEXT, gidilecek_yer TEXT, tel TEXT, fiyat REAL, durum TEXT DEFAULT "Havuzda", kurye_id INTEGER)')

@app.route('/') # Yönetici Paneli
def index():
    with get_db() as conn:
        kuryeler = conn.execute('SELECT * FROM kuryeler').fetchall()
    return render_template('index.html', kuryeler=kuryeler)

@app.route('/kurye_panel', methods=['GET', 'POST']) # Kurye Giriş ve Havuz
def kurye_panel():
    if 'kurye_id' not in session:
        if request.method == 'POST':
            tel = request.form['tel']
            with get_db() as conn:
                kurye = conn.execute('SELECT * FROM kuryeler WHERE tel = ? AND durum = "Aktif"', (tel,)).fetchone()
                if kurye:
                    session['kurye_id'] = kurye['id']
                    return redirect(url_for('kurye_panel'))
                return "Hata: Kurye bulunamadı veya henüz onaylanmadı!"
        return '''<form method="POST" style="padding:20px; background:#0f172a; color:white; height:100vh;">
                    <h2>Kurye Girişi</h2>
                    <input name="tel" placeholder="Telefon Numaranız" style="width:100%; padding:10px; margin:10px 0;">
                    <button style="width:100%; padding:15px; background:#22c55e; border:none; color:white;">GİRİŞ YAP</button>
                  </form>'''
    
    with get_db() as conn:
        havuz = conn.execute('SELECT * FROM gonderiler WHERE durum = "Havuzda"').fetchall()
        islerim = conn.execute('SELECT * FROM gonderiler WHERE kurye_id = ?', (session['kurye_id'],)).fetchall()
    return render_template('kurye_ekrani.html', havuz=havuz, islerim=islerim)

@app.route('/is_al/<int:id>')
def is_al(id):
    if 'kurye_id' in session:
        with get_db() as conn:
            conn.execute('UPDATE gonderiler SET durum = "Teslimatta", kurye_id = ? WHERE id = ? AND durum = "Havuzda"', (session['kurye_id'], id))
        return redirect(url_for('kurye_panel'))
    return redirect(url_for('kurye_panel'))

@app.route('/musteri', methods=['GET', 'POST'])
def musteri():
    if request.method == 'POST':
        with get_db() as conn:
            conn.execute('INSERT INTO gonderiler (alici_adres, gidilecek_yer, tel, fiyat) VALUES (?, ?, ?, ?)',
                         (request.form['alici_adres'], request.form['gidilecek_yer'], request.form['tel'], request.form['fiyat']))
        return "<h1>Gönderi Havuza Atıldı!</h1>"
    return render_template('musteri.html')

@app.route('/islem/<int:id>', methods=['POST'])
def islem(id):
    aksiyon = request.form.get('aksiyon')
    with get_db() as conn:
        if aksiyon == 'onayla': conn.execute('UPDATE kuryeler SET durum = "Aktif" WHERE id = ?', (id,))
        elif aksiyon == 'sil': conn.execute('DELETE FROM kuryeler WHERE id = ?', (id,))
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

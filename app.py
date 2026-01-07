import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'pajet_anahtar_99' # Oturum yönetimi için şart
DB_PATH = '/tmp/pajet_v7.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanını ve tabloları sıfırdan kur
with get_db() as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS kuryeler (id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, tel TEXT, plaka TEXT, durum TEXT DEFAULT "Onay Bekliyor", paket_sayisi INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS gonderiler (id INTEGER PRIMARY KEY AUTOINCREMENT, alici_adres TEXT, gidilecek_yer TEXT, tel TEXT, fiyat REAL, durum TEXT DEFAULT "Havuzda", kurye_id INTEGER)')

@app.route('/') # Yönetim Paneli
def index():
    with get_db() as conn:
        kuryeler = conn.execute('SELECT * FROM kuryeler').fetchall()
    return render_template('index.html', kuryeler=kuryeler)

@app.route('/kurye_panel', methods=['GET', 'POST'])
def kurye_panel():
    if 'kurye_id' not in session:
        if request.method == 'POST':
            tel = request.form.get('tel')
            with get_db() as conn:
                # Sadece durumu 'Aktif' olan kuryeler girebilir
                kurye = conn.execute('SELECT * FROM kuryeler WHERE tel = ?', (tel,)).fetchone()
                if kurye:
                    if kurye['durum'] == 'Aktif':
                        session['kurye_id'] = kurye['id']
                        return redirect(url_for('kurye_panel'))
                    else:
                        return "<h2>Hata: Hesabınız henüz yönetici tarafından ONAYLANMAMIŞ.</h2>"
                return "<h2>Hata: Bu telefon numarasıyla kayıtlı kurye bulunamadı.</h2>"
        # Giriş Formu
        return '''<body style="background:#0f172a; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh;">
                    <form method="POST" style="background:#1e293b; padding:30px; border-radius:15px; width:300px;">
                        <h3>🚚 Kurye Girişi</h3>
                        <input name="tel" placeholder="Telefon Numaranız" required style="width:100%; padding:12px; margin:10px 0; border-radius:8px; border:none;">
                        <button style="width:100%; padding:12px; background:#22c55e; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">GİRİŞ YAP</button>
                    </form></body>'''
    
    # Giriş yapılmışsa havuzu göster
    with get_db() as conn:
        havuz = conn.execute('SELECT * FROM gonderiler WHERE durum = "Havuzda"').fetchall()
        islerim = conn.execute('SELECT * FROM gonderiler WHERE kurye_id = ?', (session['kurye_id'],)).fetchall()
    return render_template('kurye_ekrani.html', havuz=havuz, islerim=islerim)

# İş Alma Rotası
@app.route('/is_al/<int:id>')
def is_al(id):
    if 'kurye_id' in session:
        with get_db() as conn:
            conn.execute('UPDATE gonderiler SET durum = "Teslimatta", kurye_id = ? WHERE id = ? AND durum = "Havuzda"', (session['kurye_id'], id))
            conn.commit()
    return redirect(url_for('kurye_panel'))

@app.route('/musteri', methods=['GET', 'POST'])
def musteri():
    if request.method == 'POST':
        with get_db() as conn:
            conn.execute('INSERT INTO gonderiler (alici_adres, gidilecek_yer, tel, fiyat) VALUES (?, ?, ?, ?)',
                         (request.form['alici_adres'], request.form['gidilecek_yer'], request.form['tel'], request.form['fiyat']))
            conn.commit()
        return "<h1>Gönderi Alındı!</h1><script>setTimeout(()=> window.location.href='/musteri', 2000);</script>"
    return render_template('musteri.html')

@app.route('/islem/<int:id>', methods=['POST'])
def islem(id):
    aksiyon = request.form.get('aksiyon')
    with get_db() as conn:
        if aksiyon == 'onayla': conn.execute('UPDATE kuryeler SET durum = "Aktif" WHERE id = ?', (id,))
        elif aksiyon == 'sil': conn.execute('DELETE FROM kuryeler WHERE id = ?', (id,))
        conn.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

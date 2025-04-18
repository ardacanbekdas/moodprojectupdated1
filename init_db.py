import sqlite3

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Kullanıcılar Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

    # Favori Şarkılar Tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        track_id TEXT NOT NULL,
        track_name TEXT,
        track_artist TEXT,
        track_album_name TEXT,
        image_url TEXT,
        spotify_link TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

# Bu fonksiyonu bir kez çalıştırarak veritabanı ve tabloları oluştur
init_db()
import sqlite3

# Veritabanı bağlantısı aç
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Favori şarkıları çek
cursor.execute("SELECT * FROM favorites")
favorites = cursor.fetchall()

# Verileri yazdır
for fav in favorites:
    print(fav)

# Bağlantıyı kapat
conn.close()

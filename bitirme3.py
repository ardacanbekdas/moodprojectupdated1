from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from flask_session import Session
import pandas as pd
import sqlite3
import os
import webbrowser

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'super-secret-spotify-key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

oauth = OAuth(app)


# CSV verisi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR, "song.csv"))
df.dropna(subset=["track_name", "track_artist", "track_album_name", "track_id"], inplace=True)


def get_spotify_link(track_id):
    return f"https://open.spotify.com/track/{track_id}"


# Ruh haline göre şarkı
def get_mood_based_songs(mood):
    if mood == "mutlu":
        filtered = df[(df['valence'] > 0.7) & (df['energy'] > 0.7)]
    elif mood == "üzgün":
        filtered = df[(df['valence'] < 0.4) & (df['energy'] < 0.5)]
    elif mood == "sakin":
        filtered = df[(df['tempo'] < 100) & (df['acousticness'] > 0.5)]
    elif mood == "enerjik":
        filtered = df[(df['tempo'] > 120) & (df['danceability'] > 0.7)]
    elif mood == "romantik":
        filtered = df[(df['valence'] > 0.4) & (df['valence'] < 0.7) & (df['acousticness'] > 0.4) & (df['energy'] < 0.6)]
    elif mood == "yaz":
        filtered = df[(df['valence'] > 0.7) & (df['danceability'] > 0.7) & (df['energy'] > 0.6)]
    else:
        filtered = df

    result = filtered.sample(n=6) if not filtered.empty else df.sample(n=6)
    result["spotify_link"] = result["track_id"].apply(get_spotify_link)
    return result


# SQLite: kullanıcıyı e-postayla al
def get_user_by_email(email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))


@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    moods = {
        "mutlu": "😊",
        "üzgün": "😢",
        "sakin": "😌",
        "enerjik": "⚡",
        "romantik": "💖",
        "yaz": "☀️"
    }
    genres = df['playlist_genre'].dropna().unique().tolist()
    return render_template("moods.html", moods=moods, genres=genres)


@app.route('/recommendation')
def recommendation():
    mood = request.args.get("mood")
    genre = request.args.get("genre")

    genre_display_names = {
        "edm": "Electronic",
        "r&b": "Blues",
        "pop": "Pop",
        "rock": "Rock",
        "rap": "Rap",
        "latin": "Latin"
    }

    if genre:
        filtered = df[df["playlist_genre"].str.lower() == genre.lower()]
        result = filtered.sample(n=6) if not filtered.empty else df.sample(n=6)
        result["spotify_link"] = result["track_id"].apply(get_spotify_link)
        display_mood = genre_display_names.get(genre.lower(), genre.capitalize())
        return render_template("recommendation.html", songs=result.to_dict(orient="records"), display_mood=display_mood)

    if mood:
        recommended = get_mood_based_songs(mood)
        return render_template("recommendation.html", songs=recommended.to_dict(orient="records"), display_mood=mood)

    return "Geçerli bir ruh hali veya tür seçilmedi.", 400


@app.route('/face')
def face():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("face.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                           (username, email, password_hash))
            conn.commit()
            flash('Kayıt başarılı! Giriş yapabilirsin.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Bu e-posta veya kullanıcı adı zaten kayıtlı.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash(f'Hoş geldin {user[1]}!', 'success')
            return redirect('/home')
        else:
            flash('Geçersiz e-posta veya şifre.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Çıkış yaptınız.', 'info')
    return redirect(url_for('login'))


# Favori şarkıları gösterme
@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Eğer kullanıcı giriş yapmamışsa login'e yönlendir

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM favorites WHERE user_id = ?", (session['user_id'],))
    favorites = cursor.fetchall()  # Kullanıcının favori şarkılarını al
    conn.close()

    return render_template("favorites.html", favorites=favorites)  # favorites.html sayfasına gönder


# Favori şarkı ekleme
@app.route('/favorite', methods=['POST'])
def favorite():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Eğer kullanıcı giriş yapmamışsa login'e yönlendir

    user_id = session['user_id']
    data = request.form

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO favorites (user_id, track_id, track_name, track_artist, track_album_name, image_url, spotify_link)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        data['track_id'],
        data['track_name'],
        data['track_artist'],
        data['track_album_name'],
        data['image_url'],  # Kapak fotoğrafı URL'si
        data['spotify_link']  # Spotify linki
    ))
    conn.commit()
    conn.close()
    flash("Şarkı favorilere eklendi!", "success")
    return redirect(request.referrer)  # Kullanıcıyı tekrar bulunduğu sayfaya yönlendir



oauth.register(
    name='google',
    client_id='72352510959-11a06nrsogchgpgir6tjkemmn2k7hv70.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)




oauth.register(
    name='spotify',
    client_id='a57417011dcb4b98b7445ffc453b27d0',
    client_secret='ce2cbac13ecf4f26acc82bd5a76306ce',
    access_token_url='https://accounts.spotify.com/api/token',
    authorize_url='https://accounts.spotify.com/authorize',
    api_base_url='https://api.spotify.com/v1/',
    client_kwargs={'scope': 'user-read-email'}
)


@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)

    # nonce'i session'a koyuyoruz
    from uuid import uuid4
    session['nonce'] = uuid4().hex

    return oauth.google.authorize_redirect(redirect_uri, nonce=session['nonce'])


@app.route('/authorize/google')
def authorize_google():
    token = oauth.google.authorize_access_token()

    # nonce kontrolü burada
    user_info = oauth.google.parse_id_token(token, nonce=session.get('nonce'))

    email = user_info['email']
    name = user_info.get('name', 'GoogleUser')

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                       (name, email, 'oauth'))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

    conn.close()

    session['user_id'] = user[0]
    session['username'] = user[1]

    return redirect(url_for('home'))


# Favori şarkıyı silme
@app.route('/delete_favorite/<int:song_id>', methods=['GET'])
def delete_favorite(song_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE id = ? AND user_id = ?", (song_id, session['user_id']))
    conn.commit()
    conn.close()
    flash("Şarkı favorilerden kaldırıldı!", "success")
    return redirect(url_for('favorites'))


@app.route('/login/spotify')
def login_spotify():
    redirect_uri = url_for('authorize_spotify', _external=True)
    return oauth.spotify.authorize_redirect(redirect_uri)

@app.route('/authorize/spotify')
def authorize_spotify():
    token = oauth.spotify.authorize_access_token()
    resp = oauth.spotify.get('me')
    profile = resp.json()

    email = profile.get('email', f"{profile['id']}@spotify.com")  # Spotify bazen email vermez
    name = profile.get('display_name', 'SpotifyUser')

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                       (name, email, 'oauth'))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

    conn.close()

    session['user_id'] = user[0]
    session['username'] = user[1]

    return redirect(url_for('home'))

if __name__ == '__main__':
    import webbrowser
    webbrowser.open("http://127.0.0.1:5050/")
    app.run(debug=True, port=5050, use_reloader=False)

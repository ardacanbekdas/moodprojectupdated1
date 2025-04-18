import pandas as pd
import random

# CSV dosyasını oku
df = pd.read_csv("songs_normalize.csv")

# Kullanıcıdan ruh hali al
mood = input("Bugünkü ruh haliniz nedir? (Mutlu, Üzgün, Sakin, Enerjik): ").strip().lower()


# Ruh haline göre filtreleme kriterleri
def get_mood_based_songs(mood):
    if mood == "mutlu":
        filtered_songs = df[(df['valence'] > 0.7) & (df['energy'] > 0.7)]
    elif mood == "üzgün":
        filtered_songs = df[(df['valence'] < 0.4) & (df['energy'] < 0.5)]
    elif mood == "sakin":
        filtered_songs = df[(df['tempo'] < 100) & (df['acousticness'] > 0.5)]
    elif mood == "enerjik":
        filtered_songs = df[(df['tempo'] > 120) & (df['danceability'] > 0.7)]
    else:
        print("Geçersiz ruh hali girdiniz. Varsayılan olarak popüler şarkılar öneriliyor.")
        filtered_songs = df.sort_values(by='popularity', ascending=False)

    return filtered_songs.sample(n=10) if not filtered_songs.empty else df.sample(n=5)


# Önerilen şarkıları getir
recommended_songs = get_mood_based_songs(mood)

# Şarkıları yazdır
print("\nÖnerilen Şarkılar:")
for idx, row in recommended_songs.iterrows():
    print(f"{row['song']} - {row['artist']} (Enerji: {row['energy']:.2f}, Valence: {row['valence']:.2f})")

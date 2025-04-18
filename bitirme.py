import pandas as pd

df = pd.read_csv("song.csv")

df.dropna(subset=["track_name", "track_artist", "track_album_name"], inplace=True)

print(df.isna().sum())
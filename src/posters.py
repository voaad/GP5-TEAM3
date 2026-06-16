import time
import requests
import pandas as pd
from pathlib import Path

BASE_URL = "https://image.tmdb.org/t/p/w500"
SAVE_DIR = Path("data/raw/posters/downloaded")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

def get_downloaded_ids():
    return {f.stem for f in SAVE_DIR.glob("*.jpg")}

def mark_downloaded(df):
    df['downloaded'] = df['id'].astype(str).isin(get_downloaded_ids())
    return df

def download_poster(movie_id, poster_path):
    url = BASE_URL + str(poster_path)
    filename = SAVE_DIR / "{}.jpg".format(movie_id)
    try:
        resp = requests.get(url, timeout=(5, 15))
        if resp.status_code == 200:
            filename.write_bytes(resp.content)
        else:
            print("Статус {} для фильма {}".format(resp.status_code, movie_id))
    except requests.exceptions.Timeout:
        print("Timeout, пропускаем {}".format(movie_id))
    except Exception as e:
        print("Ошибка на фильме {}: {}".format(movie_id, e))

# загружаем данные и проверяем что уже скачалось
df = pd.read_csv("data/processed/tmdb_clean1.csv")
df = mark_downloaded(df)

print("Текущий баланс:")
print(df.groupby('primary_genre')['downloaded'].sum())

# докачиваем недостающее
to_download = df[~df['downloaded']]
total = len(to_download)
print("\nК докачке: {}".format(total))

for idx, (i, row) in enumerate(to_download.iterrows(), start=1):
    download_poster(row['id'], row['poster_path'])

    if idx % 100 == 0:
        print("Докачано: {}/{}".format(idx, total))

    time.sleep(0.2)

# проверка
df = mark_downloaded(df)
print("\nБаланс после докачки:")
genre_counts = df.groupby('primary_genre')['downloaded'].sum()
print(genre_counts)

# балансировка по жанру с минимумом постеров
MIN_COUNT = genre_counts.min()
print("\nМинимум по жанрам: {}".format(MIN_COUNT))

df_downloaded = df[df['downloaded']]
parts = [
    group.sample(min(len(group), MIN_COUNT), random_state=42)
    for i, group in df_downloaded.groupby('primary_genre')
]
df_final = pd.concat(parts).reset_index(drop=True)

df_final.to_csv("data/processed/tmdb_cv.csv", index=False)
print("\nВ итоге получилось: {} строк".format(len(df_final)))
print(df_final['primary_genre'].value_counts())
import requests, time
import pandas as pd
from pathlib import Path

df = pd.read_csv("data/processed/tmdb_clean1.csv")
save_dir = Path("data/raw/posters/downloaded")
save_dir.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://image.tmdb.org/t/p/w500"

# Что уже скачано
existing_ids = set()
for f in save_dir.glob("*.jpg"):
    existing_ids.add(f.stem)
df['downloaded'] = df['id'].astype(str).isin(existing_ids)

print("Текущий баланс:")
print(df.groupby('primary_genre')['downloaded'].sum())

# Докачиваем недостающее
to_download = df[~df['downloaded']]
print("\nК докачке: " + str(len(to_download)))

idx = 0
for _, row in to_download.iterrows():
    idx += 1
    filename = save_dir / (str(row['id']) + ".jpg")

    url = BASE_URL + str(row["poster_path"])
    try:
        resp = requests.get(url, timeout=(5, 15))
        if resp.status_code == 200:
            filename.write_bytes(resp.content)
        else:
            print("Статус " + str(resp.status_code) + " для фильма " + str(row['id']))
    except requests.exceptions.Timeout:
        print("Timeout, пропускаем " + str(row['id']))
        continue
    except Exception as e:
        print("Ошибка на фильме " + str(row['id']) + ": " + str(e))
        continue

    if idx % 100 == 0:
        print("Докачано: " + str(idx) + "/" + str(len(to_download)))

    time.sleep(0.2)

# Финальная проверка
existing_ids = set()
for f in save_dir.glob("*.jpg"):
    existing_ids.add(f.stem)
df['downloaded'] = df['id'].astype(str).isin(existing_ids)

print("\nБаланс после докачки:")
genre_counts = df.groupby('primary_genre')['downloaded'].sum()
print(genre_counts)

# Сохраняем итоговый сбалансированный список (минимум по жанрам)
MIN_COUNT = genre_counts.min()
print("\nМинимум по жанрам: " + str(MIN_COUNT))

df_downloaded = df[df['downloaded']]
parts = []
for genre, group in df_downloaded.groupby('primary_genre'):
    n = len(group)
    if n > MIN_COUNT:
        n = MIN_COUNT
    parts.append(group.sample(n, random_state=42))

df_final = pd.concat(parts).reset_index(drop=True)

df_final.to_csv("data/processed/tmdb_cv.csv", index=False)
print("\nИтоговый сбалансированный датасет: " + str(len(df_final)) + " строк")
print(df_final['primary_genre'].value_counts())
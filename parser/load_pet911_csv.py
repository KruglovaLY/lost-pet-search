import hashlib
import os
import sqlite3
from pathlib import Path

import pandas as pd
import requests


DB_PATH = "pets.db"
CSV_PATH = "data/pet911_links.csv"
IMAGES_DIR = "data/images"

DEFAULT_CAT_IMAGE = "data/images/cat_1.jpg"
DEFAULT_DOG_IMAGE = "data/images/dog_1.jpg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 LostPetSearchStudentProject/1.0"
}


def create_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT,
            name TEXT NOT NULL,
            animal_type TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            image_path TEXT NOT NULL,
            source_url TEXT UNIQUE
        )
        """
    )


def download_image(image_url: str, source_url: str) -> str:
    if not isinstance(image_url, str):
        return ""

    if not image_url.startswith("http"):
        return ""

    Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)

    image_hash = hashlib.md5(source_url.encode("utf-8")).hexdigest()
    image_path = os.path.join(IMAGES_DIR, f"pet911_{image_hash}.jpg")

    if os.path.exists(image_path):
        return image_path

    response = requests.get(image_url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")

    if "image" not in content_type:
        return ""

    with open(image_path, "wb") as file:
        file.write(response.content)

    return image_path


def get_fallback_image(animal_type: str) -> str:
    if animal_type == "Кошка":
        return DEFAULT_CAT_IMAGE

    if animal_type == "Собака":
        return DEFAULT_DOG_IMAGE

    return DEFAULT_CAT_IMAGE


def main():
    df = pd.read_csv(CSV_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    create_table(cursor)

    cursor.execute("DELETE FROM pets")

    saved = 0
    downloaded = 0
    fallback_used = 0

    for _, row in df.iterrows():
        source_url = str(row["source_url"])
        image_url = str(row.get("image_url", ""))
        animal_type = str(row["animal_type"])

        try:
            image_path = download_image(image_url, source_url)
        except Exception as error:
            print(f"Не удалось скачать картинку: {image_url}. Ошибка: {error}")
            image_path = ""

        if image_path:
            downloaded += 1
        else:
            image_path = get_fallback_image(animal_type)
            fallback_used += 1

        external_id = hashlib.md5(source_url.encode("utf-8")).hexdigest()

        cursor.execute(
            """
            INSERT OR IGNORE INTO pets
            (external_id, name, animal_type, location, description, image_path, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                external_id,
                str(row["title"])[:80],
                animal_type,
                str(row["location"]),
                str(row["description"]),
                image_path,
                source_url,
            ),
        )

        saved += 1

    conn.commit()
    conn.close()

    print(f"Готово. Загружено записей в базу: {saved}")
    print(f"Картинок скачано: {downloaded}")
    print(f"Использовано fallback-картинок: {fallback_used}")


if __name__ == "__main__":
    main()
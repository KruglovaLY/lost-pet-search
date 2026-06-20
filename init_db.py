import sqlite3


DB_PATH = "pets.db"


pets = [
    {
        "name": "Барсик",
        "animal_type": "Кот",
        "location": "Москва, Вешняки",
        "description": "Серый кот с белой грудкой. Потерян рядом с жилым районом.",
        "image_path": "data/images/cat_1.jpg",
        "source_url": "https://pet911.ru/moskva",
    },
    {
        "name": "Мурка",
        "animal_type": "Кошка",
        "location": "Москва, Измайлово",
        "description": "Трехцветная кошка среднего размера.",
        "image_path": "data/images/cat_2.jpg",
        "source_url": "https://pet911.ru/moskva",
    },
    {
        "name": "Рекс",
        "animal_type": "Собака",
        "location": "Москва, Сокольники",
        "description": "Коричневая собака среднего размера, висячие уши.",
        "image_path": "data/images/dog_1.jpg",
        "source_url": "https://pet911.ru/moskva",
    },
    {
        "name": "Белка",
        "animal_type": "Собака",
        "location": "Москва, Марьино",
        "description": "Небольшая белая пушистая собака.",
        "image_path": "data/images/dog_2.jpg",
        "source_url": "https://pet911.ru/moskva",
    },
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            animal_type TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT,
            image_path TEXT NOT NULL,
            source_url TEXT
        )
    """)

    cursor.execute("DELETE FROM pets")

    for pet in pets:
        cursor.execute("""
            INSERT INTO pets 
            (name, animal_type, location, description, image_path, source_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            pet["name"],
            pet["animal_type"],
            pet["location"],
            pet["description"],
            pet["image_path"],
            pet["source_url"],
        ))

    conn.commit()
    conn.close()

    print("База pets.db создана")


if __name__ == "__main__":
    init_db()
import sqlite3


DB_PATH = "pets.db"


def get_all_pets():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT id, name, animal_type, location, description, image_path, source_url
        FROM pets
        '''
    )

    pets = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return pets

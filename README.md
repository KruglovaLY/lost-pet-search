# Lost Pet Search

Учебный ML-сервис для поиска животных в картотеках потерянных животных по фотографии.

## Описание

Пользователь загружает фотографию животного через Streamlit-интерфейс.  
Frontend отправляет изображение в FastAPI backend.  
Backend сравнивает изображение с локальной базой животных и возвращает наиболее похожие записи.

## Архитектура

- `frontend/` — интерфейс на Streamlit
- `backend/` — API на FastAPI
- `backend/ml.py` — ML-логика сравнения изображений
- `backend/database.py` — работа с SQLite
- `init_db.py` — создание базы данных
- `data/images/` — изображения животных
- `pets.db` — SQLite-база

## Технологии

- Python
- Streamlit
- FastAPI
- SQLite
- PyTorch
- Torchvision
- ResNet18
- Pillow
- Pandas
- Requests

## ML-часть

Для сравнения изображений используется предобученная модель ResNet18.  
Модель преобразует каждое изображение в числовой вектор признаков.  
После этого рассчитывается cosine similarity между загруженным фото и изображениями из базы.

## Установка

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
import os

import pandas as pd
import requests
import streamlit as st
from PIL import Image


API_URL = "http://localhost:8000"


st.set_page_config(
    page_title="Lost Pet Search",
    page_icon="🐾",
    layout="wide",
)


st.title("🐾 Поиск животных по фотографии")

st.write(
    '''
    Учебный сервис для поиска похожих животных в картотеке потерянных животных.

    Архитектура проекта:
    - frontend: Streamlit
    - backend: FastAPI
    - база данных: SQLite
    - ML-логика: сравнение изображений по цветовым признакам
    '''
)


def is_backend_available():
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


with st.sidebar:
    st.header("Настройки поиска")

    top_k = st.slider(
        "Количество результатов",
        min_value=1,
        max_value=10,
        value=5,
    )

    animal_type = st.selectbox(
        "Тип животного",
        ["Все", "Кот", "Кошка", "Собака"],
    )

    st.markdown("---")
    st.write("Backend:")
    st.code(API_URL)


if not is_backend_available():
    st.error("Backend не запущен. Запустите команду: uvicorn backend.api:app --reload")
    st.stop()


st.success("Backend FastAPI доступен")


tab_search, tab_database, tab_about = st.tabs(
    [
        "🔎 Поиск",
        "📋 База",
        "ℹ️ О проекте",
    ]
)


with tab_search:
    uploaded_file = st.file_uploader(
        "Загрузите фото животного",
        type=["jpg", "jpeg", "png"],
    )

    if uploaded_file is None:
        st.info("Загрузите фотографию, чтобы начать поиск.")
    else:
        image = Image.open(uploaded_file)

        col_left, col_right = st.columns([1, 2])

        with col_left:
            st.subheader("Загруженное фото")
            st.image(image, use_container_width=True)

        with col_right:
            st.subheader("Результаты поиска")

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            }

            data = {
                "top_k": top_k,
                "animal_type": animal_type,
            }

            with st.spinner("Ищем похожих животных..."):
                response = requests.post(
                    f"{API_URL}/search",
                    files=files,
                    data=data,
                    timeout=60,
                )

            if response.status_code != 200:
                st.error("Ошибка поиска")
                st.write(response.text)
            else:
                results = response.json()["results"]

                if not results:
                    st.warning("Похожие животные не найдены.")
                else:
                    st.success(f"Найдено результатов: {len(results)}")

                    chart_data = pd.DataFrame(
                        {
                            "Животное": [item["name"] for item in results],
                            "Похожесть": [
                                item["similarity_percent"]
                                for item in results
                            ],
                        }
                    ).set_index("Животное")

                    st.subheader("График похожести")
                    st.bar_chart(chart_data)

                    st.subheader("Карточки животных")

                    for item in results:
                        with st.container():
                            col_image, col_text = st.columns([1, 3])

                            with col_image:
                                if os.path.exists(item["image_path"]):
                                    st.image(
                                        item["image_path"],
                                        use_container_width=True,
                                    )
                                else:
                                    st.warning("Фото не найдено")

                            with col_text:
                                st.markdown(f"### {item['name']}")
                                st.write(f"**Тип:** {item['animal_type']}")
                                st.write(f"**Локация:** {item['location']}")
                                st.write(f"**Описание:** {item['description']}")
                                st.write(
                                    f"**Похожесть:** "
                                    f"{item['similarity_percent']}%"
                                )

                                st.progress(
                                    max(
                                        0.0,
                                        min(float(item["similarity"]), 1.0),
                                    )
                                )

                                if item.get("source_url"):
                                    st.markdown(
                                        f"[Открыть источник]({item['source_url']})"
                                    )

                            st.markdown("---")


with tab_database:
    st.subheader("База животных")

    response = requests.get(f"{API_URL}/pets")

    if response.status_code != 200:
        st.error("Не удалось получить данные из backend.")
    else:
        pets = response.json()["items"]

        st.write(f"Количество записей: **{len(pets)}**")

        for pet in pets:
            with st.container():
                col_image, col_text = st.columns([1, 3])

                with col_image:
                    if os.path.exists(pet["image_path"]):
                        st.image(
                            pet["image_path"],
                            use_container_width=True,
                        )
                    else:
                        st.warning("Фото не найдено")

                with col_text:
                    st.markdown(f"### {pet['name']}")
                    st.write(f"**Тип:** {pet['animal_type']}")
                    st.write(f"**Локация:** {pet['location']}")
                    st.write(f"**Описание:** {pet['description']}")

                    if pet.get("source_url"):
                        st.markdown(f"[Источник]({pet['source_url']})")

                st.markdown("---")


with tab_about:
    st.subheader("О проекте")

    st.write(
        '''
        Проект показывает минимальную архитектуру ML-сервиса.

        Пользователь загружает изображение во frontend на Streamlit.
        Frontend отправляет файл в backend на FastAPI.
        Backend получает данные из SQLite-базы и сравнивает изображение
        с изображениями животных из базы.

        В упрощенной версии сравнение выполняется по цветовой гистограмме:
        каждое изображение переводится в числовой вектор, после чего считается
        cosine similarity.
        '''
    )

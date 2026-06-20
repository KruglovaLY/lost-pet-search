import os

import pandas as pd
import requests
import streamlit as st
from PIL import Image


API_URL = "http://localhost:8000"


st.set_page_config(
    page_title="Поиск потерянных животных",
    page_icon="🐾",
    layout="wide",
)


st.title("🐾 Поиск животных в картотеках потерянных животных")

st.write(
    '''
    Проект демонстрирует сервис поиска похожих животных по фотографии.

    Архитектура:
    - Frontend: Streamlit
    - Backend: FastAPI
    - База данных: SQLite
    - ML-модель: ResNet18
    '''
)


with st.sidebar:
    st.header("Настройки")

    top_k = st.slider(
        "Количество результатов",
        min_value=1,
        max_value=10,
        value=4,
    )

    animal_type = st.selectbox(
        "Тип животного",
        ["Все", "Кот", "Кошка", "Собака"],
    )


def backend_available():
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


if not backend_available():
    st.error("Backend не запущен. Запустите: uvicorn backend.api:app --reload")
    st.stop()


st.success("Backend FastAPI доступен")


tab_search, tab_db, tab_about = st.tabs(
    [
        "🔎 Поиск по фото",
        "📋 База животных",
        "ℹ️ О проекте",
    ]
)


with tab_search:
    uploaded_file = st.file_uploader(
        "Загрузите фотографию животного",
        type=["jpg", "jpeg", "png"],
    )

    if uploaded_file is None:
        st.info("Загрузите фото, чтобы начать поиск.")
    else:
        uploaded_image = Image.open(uploaded_file)

        left_col, right_col = st.columns([1, 2])

        with left_col:
            st.subheader("Загруженное фото")
            st.image(uploaded_image, use_container_width=True)

        with right_col:
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

            with st.spinner("Отправляем фото в backend и ищем похожие объявления..."):
                response = requests.post(
                    f"{API_URL}/search",
                    files=files,
                    data=data,
                    timeout=120,
                )

            if response.status_code != 200:
                st.error("Ошибка поиска")
                st.write(response.text)
            else:
                results = response.json()["results"]

                if len(results) == 0:
                    st.warning("Похожие животные не найдены.")
                else:
                    st.success(f"Найдено результатов: {len(results)}")

                    chart_df = pd.DataFrame(
                        {
                            "Животное": [
                                item["name"]
                                for item in results
                            ],
                            "Похожесть": [
                                item["similarity_percent"]
                                for item in results
                            ],
                        }
                    ).set_index("Животное")

                    st.subheader("График похожести")
                    st.bar_chart(chart_df)

                    st.subheader("Похожие объявления")

                    for item in results:
                        with st.container():
                            col1, col2 = st.columns([1, 3])

                            with col1:
                                image_path = item["image_path"]

                                if os.path.exists(image_path):
                                    st.image(
                                        image_path,
                                        use_container_width=True,
                                    )
                                else:
                                    st.warning("Фото не найдено")

                            with col2:
                                st.markdown(f"### {item['name']}")
                                st.write(f"**Тип:** {item['animal_type']}")
                                st.write(f"**Локация:** {item['location']}")
                                st.write(f"**Описание:** {item['description']}")
                                st.write(
                                    f"**Похожесть:** "
                                    f"{item['similarity_percent']}%"
                                )

                                progress_value = max(
                                    0.0,
                                    min(float(item["similarity"]), 1.0),
                                )

                                st.progress(progress_value)

                                if item["similarity_percent"] >= 80:
                                    st.success("Высокое сходство")
                                elif item["similarity_percent"] >= 50:
                                    st.warning("Среднее сходство")
                                else:
                                    st.info("Низкое сходство")

                                if item.get("source_url"):
                                    st.markdown(
                                        f"[Источник]({item['source_url']})"
                                    )

                            st.markdown("---")


with tab_db:
    st.subheader("База животных")

    response = requests.get(f"{API_URL}/pets")

    if response.status_code == 200:
        pets = response.json()["items"]

        st.write(f"Количество записей: **{len(pets)}**")

        for pet in pets:
            with st.container():
                col1, col2 = st.columns([1, 3])

                with col1:
                    image_path = pet["image_path"]

                    if os.path.exists(image_path):
                        st.image(image_path, use_container_width=True)
                    else:
                        st.warning("Фото не найдено")

                with col2:
                    st.markdown(f"### {pet['name']}")
                    st.write(f"**Тип:** {pet['animal_type']}")
                    st.write(f"**Локация:** {pet['location']}")
                    st.write(f"**Описание:** {pet['description']}")

                    if pet.get("source_url"):
                        st.markdown(f"[Источник]({pet['source_url']})")

                st.markdown("---")
    else:
        st.error("Не удалось получить данные из backend.")


with tab_about:
    st.subheader("Описание проекта")

    st.write(
        '''
        Этот проект реализует минимальный ML-сервис для поиска животных
        в картотеке потерянных животных.

        Пользователь загружает фотографию через Streamlit.
        Frontend отправляет изображение в FastAPI backend.
        Backend получает список животных из SQLite-базы и сравнивает фотографии
        с помощью предобученной модели ResNet18.

        Результаты сортируются по cosine similarity и возвращаются во frontend.
        '''
    )

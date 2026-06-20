import os
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

import torch
import torchvision.models as models
import torchvision.transforms as transforms

from sklearn.metrics.pairwise import cosine_similarity


st.set_page_config(
    page_title="Поиск потерянных животных",
    page_icon="🐾",
    layout="wide"
)


@st.cache_resource
def load_model():
    """
    Загружает предобученную модель ResNet18.
    Последний слой заменяется, чтобы получать не класс изображения,
    а числовой вектор признаков.
    """
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = torch.nn.Identity()
    model.eval()
    return model


@st.cache_data
def load_data():
    """
    Загружает таблицу с базой животных.
    """
    return pd.read_csv("pets.csv")


def preprocess_image(image):
    """
    Подготавливает изображение для нейросети.
    """
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    image = image.convert("RGB")
    tensor = transform(image).unsqueeze(0)
    return tensor


def get_embedding(image, model):
    """
    Получает числовой вектор изображения.
    """
    tensor = preprocess_image(image)

    with torch.no_grad():
        embedding = model(tensor)

    return embedding.numpy()


def build_database_embeddings(df, model):
    """
    Создает векторы для всех изображений из базы.
    """
    embeddings = []

    for image_path in df["image_path"]:
        if os.path.exists(image_path):
            image = Image.open(image_path)
            embedding = get_embedding(image, model)
            embeddings.append(embedding[0])
        else:
            embeddings.append(np.zeros(512))

    return np.array(embeddings)


def find_similar_pets(uploaded_image, df, database_embeddings, model, top_k=5):
    """
    Сравнивает загруженное изображение с изображениями из базы.
    """
    uploaded_embedding = get_embedding(uploaded_image, model)

    similarities = cosine_similarity(
        uploaded_embedding,
        database_embeddings
    )[0]

    result_df = df.copy()
    result_df["similarity"] = similarities

    result_df = result_df.sort_values(
        by="similarity",
        ascending=False
    ).head(top_k)

    return result_df


st.title("🐾 Поиск потерянных животных по фотографии")

st.write(
    """
    Это учебное приложение сравнивает загруженное фото животного 
    с локальной базой объявлений и показывает наиболее похожие варианты.
    """
)


model = load_model()
df = load_data()


st.sidebar.header("Настройки поиска")

top_k = st.sidebar.slider(
    "Сколько похожих объявлений показать",
    min_value=1,
    max_value=10,
    value=5
)

animal_filter = st.sidebar.selectbox(
    "Фильтр по типу животного",
    ["Все"] + sorted(df["type"].unique().tolist())
)

if animal_filter != "Все":
    df_filtered = df[df["type"] == animal_filter].reset_index(drop=True)
else:
    df_filtered = df.reset_index(drop=True)

st.sidebar.metric("Записей в базе", len(df_filtered))


uploaded_file = st.file_uploader(
    "Загрузите фотографию потерянного животного",
    type=["jpg", "jpeg", "png"]
)


if uploaded_file is not None:
    uploaded_image = Image.open(uploaded_file)

    os.makedirs("uploads", exist_ok=True)
    save_path = os.path.join("uploads", uploaded_file.name)

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"Файл загружен и сохранен: {save_path}")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Загруженное фото")
        st.image(uploaded_image, use_container_width=True)

    with col_right:
        st.subheader("Результаты поиска")

        if len(df_filtered) == 0:
            st.warning("В базе нет животных выбранного типа.")
        else:
            with st.spinner("Идет сравнение изображения с базой..."):
                database_embeddings = build_database_embeddings(df_filtered, model)

                results = find_similar_pets(
                    uploaded_image=uploaded_image,
                    df=df_filtered,
                    database_embeddings=database_embeddings,
                    model=model,
                    top_k=top_k
                )

            st.success("Поиск завершен")

            st.subheader("График похожести")

            chart_data = results[["name", "similarity"]].set_index("name")
            st.bar_chart(chart_data)

            st.subheader("Похожие объявления")

            for _, row in results.iterrows():
                similarity_percent = round(row["similarity"] * 100, 2)

                with st.container():
                    result_col1, result_col2 = st.columns([1, 3])

                    with result_col1:
                        if os.path.exists(row["image_path"]):
                            st.image(row["image_path"], use_container_width=True)
                        else:
                            st.warning("Фото не найдено")

                    with result_col2:
                        st.markdown(f"### {row['name']}")
                        st.write(f"**Тип:** {row['type']}")
                        st.write(f"**Локация:** {row['location']}")
                        st.write(f"**Описание:** {row['description']}")
                        st.write(f"**Похожесть:** {similarity_percent}%")

                        progress_value = max(0.0, min(float(row["similarity"]), 1.0))
                        st.progress(progress_value)

                        if similarity_percent >= 80:
                            st.success("Высокое сходство")
                        elif similarity_percent >= 50:
                            st.warning("Среднее сходство")
                        else:
                            st.info("Низкое сходство")

                        if pd.notna(row["url"]):
                            st.markdown(f"[Открыть источник]({row['url']})")

                    st.markdown("---")

else:
    st.info("Загрузите изображение животного, чтобы начать поиск.")

    st.subheader("Текущая база животных")

    for _, row in df_filtered.iterrows():
        with st.container():
            col1, col2 = st.columns([1, 3])

            with col1:
                if os.path.exists(row["image_path"]):
                    st.image(row["image_path"], use_container_width=True)
                else:
                    st.warning("Изображение не найдено")

            with col2:
                st.markdown(f"### {row['name']}")
                st.write(f"**Тип:** {row['type']}")
                st.write(f"**Локация:** {row['location']}")
                st.write(f"**Описание:** {row['description']}")

            st.markdown("---")
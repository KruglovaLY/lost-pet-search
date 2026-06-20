import os
import math
from PIL import Image


def image_to_vector(image):
    '''
    Преобразует изображение в простой числовой вектор.
    Используется цветовая гистограмма RGB.
    '''
    image = image.convert("RGB")
    image = image.resize((128, 128))

    histogram = image.histogram()

    total = sum(histogram)

    if total == 0:
        return histogram

    return [value / total for value in histogram]


def cosine_similarity(vector_1, vector_2):
    dot = sum(a * b for a, b in zip(vector_1, vector_2))
    norm_1 = math.sqrt(sum(a * a for a in vector_1))
    norm_2 = math.sqrt(sum(b * b for b in vector_2))

    if norm_1 == 0 or norm_2 == 0:
        return 0

    return dot / (norm_1 * norm_2)


def search_similar_pets(query_image, pets, top_k=5, animal_type="Все"):
    query_vector = image_to_vector(query_image)

    results = []

    for pet in pets:
        if animal_type != "Все" and pet["animal_type"] != animal_type:
            continue

        image_path = pet["image_path"]

        if not os.path.exists(image_path):
            continue

        try:
            pet_image = Image.open(image_path)
            pet_vector = image_to_vector(pet_image)

            similarity = cosine_similarity(query_vector, pet_vector)

            result = pet.copy()
            result["similarity"] = round(similarity, 4)
            result["similarity_percent"] = round(similarity * 100, 2)

            results.append(result)

        except Exception as error:
            print(f"Ошибка обработки изображения {image_path}: {error}")

    results = sorted(
        results,
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return results[:top_k]

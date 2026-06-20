import os
import numpy as np
from PIL import Image

import torch
import torchvision.models as models
import torchvision.transforms as transforms


model_cache = None


def load_model():
    global model_cache

    if model_cache is None:
        model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        model.fc = torch.nn.Identity()
        model.eval()
        model_cache = model

    return model_cache


def preprocess_image(image):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    image = image.convert("RGB")
    return transform(image).unsqueeze(0)


def get_embedding(image):
    model = load_model()
    tensor = preprocess_image(image)

    with torch.no_grad():
        embedding = model(tensor)

    vector = embedding.numpy()[0]

    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    return vector


def cosine_similarity(vector_1, vector_2):
    return float(np.dot(vector_1, vector_2))


def search_similar_pets(query_image, pets, top_k=5, animal_type="Все"):
    query_vector = get_embedding(query_image)

    results = []

    for pet in pets:
        if animal_type != "Все" and pet["animal_type"] != animal_type:
            continue

        image_path = pet["image_path"]

        if not os.path.exists(image_path):
            continue

        pet_image = Image.open(image_path)
        pet_vector = get_embedding(pet_image)

        similarity = cosine_similarity(query_vector, pet_vector)

        result = pet.copy()
        result["similarity"] = round(similarity, 4)
        result["similarity_percent"] = round(similarity * 100, 2)

        results.append(result)

    results = sorted(
        results,
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return results[:top_k]
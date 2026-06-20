from io import BytesIO

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from backend.database import get_all_pets
from backend.ml import search_similar_pets


app = FastAPI(
    title="Lost Pet Search API",
    description="API для поиска похожих потерянных животных по фотографии",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Lost Pet Search API работает",
        "docs": "http://localhost:8000/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/pets")
def get_pets():
    pets = get_all_pets()
    return {
        "count": len(pets),
        "items": pets,
    }


@app.post("/search")
async def search(
    file: UploadFile = File(...),
    top_k: int = Form(5),
    animal_type: str = Form("Все"),
):
    image_bytes = await file.read()
    image = Image.open(BytesIO(image_bytes))

    pets = get_all_pets()

    results = search_similar_pets(
        query_image=image,
        pets=pets,
        top_k=top_k,
        animal_type=animal_type,
    )

    return {
        "filename": file.filename,
        "top_k": top_k,
        "animal_type": animal_type,
        "results": results,
    }

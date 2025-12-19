from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import uvicorn
import logging
from typing import List
from config import MODEL, DEVICE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Загрузка модели {MODEL}...")
model = SentenceTransformer(MODEL, trust_remote_code=True, device=DEVICE)
logger.info("Модель успешно загружена!")

app = FastAPI(title="Embedding Service", version="1.0")


class EmbeddingRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    model: str = MODEL
    dimensions: int


class BatchResponse(BaseModel):
    embeddings: List[EmbeddingResponse]


@app.post("/embeddings", response_model=BatchResponse)
async def get_embedding(request: List[EmbeddingRequest]):
    """
    Эндпоинт для получения эмбеддингов текстов\n
    Принимает: [{"text": "текст1"}, {"text": "текст2"}, ...]\n
    Возвращает: {"embeddings": [EmbeddingResponse1, EmbeddingResponse2, ...]}
    """
    try:
        response_list = []
        for item in request:
            embedding = model.encode(
                [item.text], convert_to_tensor=False, show_progress_bar=False
            )[0]
            embedding_list = embedding.tolist()
            response_list.append(
                EmbeddingResponse(
                    embedding=embedding_list, dimensions=len(embedding_list)
                )
            )
        return BatchResponse(embeddings=response_list)

    except Exception as e:
        logger.error(f"Ошибка при генерации эмбеддинга: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


@app.get("/health")
async def health_check():
    """Эндпоинт для проверки работоспособности"""
    return {
        "status": "ok",
        "model": MODEL,
        "dimensions": model.get_sentence_embedding_dimension(),
    }


if __name__ == "__main__":
    uvicorn.run("embedding:app", host="0.0.0.0", port=8000, reload=False, workers=1)

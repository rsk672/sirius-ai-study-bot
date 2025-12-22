from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import logging
import sys
from typing import List
from utils.config import MODEL, DEVICE

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

logger.info(f"Загрузка модели {MODEL}...")
model = SentenceTransformer(MODEL, trust_remote_code=True, device=DEVICE)
logger.info("Модель успешно загружена!")
app = FastAPI(title="Embedding Service", version="1.0")


class BatchEmbeddingRequest(BaseModel):
    texts: List[str]


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    model: str = MODEL
    dimensions: int


class BatchResponse(BaseModel):
    embeddings: List[EmbeddingResponse]


@app.post("/embeddings", response_model=BatchResponse)
async def get_embeddings(request: BatchEmbeddingRequest):
    """
    Эндпоинт для получения эмбеддингов текстов\n
    Принимает: {"texts": ["текст1", "текст2", ...]}\n
    Возвращает: {"embeddings": [{"embedding": [...], ...}, ...]}
    """
    try:
        response_list = []
        for text in request.texts:
            embedding = model.encode(
                [text], convert_to_tensor=False, show_progress_bar=False
            )[0]
            embedding_list = embedding.tolist()
            response_list.append(
                EmbeddingResponse(
                    embedding=embedding_list, dimensions=len(embedding_list)
                )
            )
        return BatchResponse(embeddings=response_list)

    except Exception as e:
        logger.error(f"Ошибка при генерации эмбеддингов: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "model": MODEL,
        "dimensions": model.get_sentence_embedding_dimension(),
    }

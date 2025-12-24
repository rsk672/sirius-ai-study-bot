import asyncio
from models.embedding_service import RemoteEmbeddingService


async def main():
    embedder = RemoteEmbeddingService()
    texts = ["Привет мир", "Как дела?"]

    embeddings = await embedder.aembed_documents(texts)
    print(f"Получено {embeddings} эмбеддингов")
    print(f"Размерность: {len(embeddings[0])}")


if __name__ == "__main__":
    asyncio.run(main())

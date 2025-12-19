import httpx
import asyncio

async def async_get_embedding(text: str):
    url = "http://localhost:8000/embeddings"
    payload = [{"text": text}]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]
        except httpx.HTTPError as e:
            print(f"HTTP ошибка: {str(e)}")
            raise

async def main():
    embeddings = await async_get_embedding("Тестовый текст")
    embedding = embeddings[0]
    print(f"Получен эмбеддинг размерности {embedding['dimensions']}")
    print(f"Первые 3 значения: {embedding['embedding'][:3]}")

if __name__ == "__main__":
    asyncio.run(main())

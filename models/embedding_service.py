import aiohttp
from typing import List
from langchain_core.embeddings import Embeddings
from utils.config import EMBEDDING_API_URL

class RemoteEmbeddingService(Embeddings):
    def __init__(self):
        super().__init__()

    async def _call_api_async(self, texts: List[str]) -> List[List[float]]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    EMBEDDING_API_URL,
                    json={"texts": texts},
                    timeout=10
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        raise ValueError(f"API error {response.status}: {error_text}")
                    data = await response.json()
                    return [item["embedding"] for item in data["embeddings"]]
            except aiohttp.ClientError as e:
                raise ConnectionError(f"Connection failed: {str(e)}")

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        return await self._call_api_async(texts)

    async def aembed_query(self, text: str) -> List[float]:
        embeddings = await self._call_api_async([text])
        return embeddings[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor() as pool:
                    return pool.submit(
                        lambda: asyncio.run(self.aembed_documents(texts))
                    ).result()
        except RuntimeError:
            return asyncio.run(self.aembed_documents(texts))
        return asyncio.run(self.aembed_documents(texts))

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

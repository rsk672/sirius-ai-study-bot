import re
import asyncio
import time
from uvicorn import Config, Server
from utils.config import EMBEDDING_API_URL

_server = None


async def start_embedding_server() -> None:
    """Запускает сервер эмбеддингов в асинхронном режиме."""
    global _server
    match = re.search(r":(\d+)", EMBEDDING_API_URL)
    port = int(match.group(1)) if match else 8000

    config = Config(
        "models.embedding:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1,
        loop="asyncio",
        lifespan="on",
    )
    _server = Server(config)

    asyncio.create_task(_server.serve())

    await wait_for_server(port)
    
async def wait_for_server(port: int, timeout: int = 10):
    """Ждет, пока сервер станет доступен"""
    import aiohttp
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{port}/health", timeout=1) as response:
                    if response.status == 200:
                        print(f"✅ Сервер эмбеддингов доступен на порту {port}")
                        return
        except:
            await asyncio.sleep(0.5)
    raise RuntimeError(f"Сервер не запустился за {timeout} секунд")


async def stop_embedding_server() -> None:
    """Корректно останавливает сервер эмбеддингов."""
    if _server and _server.should_exit is False:
        _server.should_exit = True

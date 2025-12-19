import re
from uvicorn import Config, Server
from utils.config import EMBEDDING_API_URL

_server = None

async def start_embedding_server() -> None:
    """Запускает сервер эмбеддингов в асинхронном режиме."""
    global _server
    
    match = re.search(r':(\d+)', EMBEDDING_API_URL)
    port = int(match.group(1)) if match else 8000

    config = Config(
        "models.embedding:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1,
        loop="asyncio"
    )
    _server = Server(config)
    await _server.serve()

async def stop_embedding_server() -> None:
    """Корректно останавливает сервер эмбеддингов."""
    if _server and _server.should_exit is False:
        _server.should_exit = True

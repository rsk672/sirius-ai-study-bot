import uvicorn
from models.embedding import app
from utils.config import EMBEDDING_API_URL
from urllib.parse import urlparse

def server_main():
    """Запускает сервер в blocking-режиме (для subprocess)"""
    parsed_url = urlparse(EMBEDDING_API_URL)
    port = parsed_url.port or 8000
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="warning"
    )

if __name__ == "__main__":
    server_main()
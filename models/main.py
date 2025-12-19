import uvicorn
import re
from utils.config import EMBEDDING_API_URL

if __name__ == "__main__":
    match = re.search(r':(\d+)', EMBEDDING_API_URL)
    port = int(match.group(1)) if match else 8000

    uvicorn.run(
        "models.embedding:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1
    )

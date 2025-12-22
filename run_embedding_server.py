import asyncio
import logging
import sys
from dotenv import load_dotenv


from models.main import server_main


async def main() -> None:
    embedding_task = asyncio.create_task(server_main())
    await asyncio.sleep(3)
    await embedding_task


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Приложение остановлено пользователем")

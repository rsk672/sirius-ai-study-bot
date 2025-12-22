import asyncio
import logging
import sys
from dotenv import load_dotenv


from models.main import start_embedding_server, stop_embedding_server
from bot.handlers import bot, dp


async def main() -> None:
    embedding_task = asyncio.create_task(start_embedding_server())

    await asyncio.sleep(3)
    
    try:
        await dp.start_polling(bot)
    finally:
        await stop_embedding_server()
        await embedding_task


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Приложение остановлено пользователем")

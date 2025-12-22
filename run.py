import asyncio
import logging
import sys
import subprocess
import atexit
from dotenv import load_dotenv
from bot.handlers import bot, dp


async def main():
    server_process = subprocess.Popen(
        [sys.executable, "-c", "from models.main import server_main; server_main()"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logging.info("🚀 Запущен сервер эмбеддингов в subprocess")

    try:
        await dp.start_polling(bot)
    finally:
        server_process.terminate()
        server_process.wait(timeout=5)
        server_process.kill()


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    asyncio.run(main())

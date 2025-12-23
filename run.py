import asyncio
import logging
import sys
from dotenv import load_dotenv
from bot.handlers import bot, dp


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    asyncio.run(main())

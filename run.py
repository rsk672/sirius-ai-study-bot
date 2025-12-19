# import os
# if __name__ == '__main__':
#     os.system('python bot\\handlers.py')
import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from dotenv import load_dotenv

from aiogram.types import Message, FSInputFile

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import time


from bot.handlers import bot, dp

async def main() -> None:
    global dp
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
#Empty comment

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

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

files_dir = 'data\\files'

strings = {'main' : 'Главная', 'load' : 'Загрузить', 'ask' : 'Спросить', 'back' : 'Главная',
         'hi' : 'Я суперпупермегаумный бот.', 'request_pdf' : 'Отправьте PDF-файл или введите текст',
           'success' : 'Файл успешно сохранён. Хотите отправить еще?', 'noinput' : 'Отправьте непустое сообщение!',
           'pleasereset' : 'Пожалуйста, нажмите кнопку "Главная" внизу.', 'tba' : 'Такой функции у нас пока нет(('}

'''@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")
'''

#Главная клавиатура - Загрузить и Спросить
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=strings["ask"], request_location=False))
    builder.add(KeyboardButton(text=strings["load"], request_location=False))
    builder.add(KeyboardButton(text=strings["back"], request_location=False))
    builder.adjust(2, 1) 
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        #input_field_placeholder="Выберите действие..."
    )

#Клавиатура, когда пользователь отправляет пдф, только назад
def get_empty_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=strings["back"], request_location=False))
    builder.adjust(2, 1)
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        #input_field_placeholder="Выберите действие..."
    )

user_states = {}
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        strings["hi"],
        reply_markup=get_main_keyboard()
    )

@dp.message(lambda message: message.text == strings["load"])
async def handle_upload_button(message: Message):
    user_states[message.from_user.id] = 'awaiting_pdf'
    await message.answer(
        strings['request_pdf'],
        reply_markup=get_empty_keyboard()
    )
    

@dp.message(lambda message: message.text == strings["ask"])
async def handle_upload_button(message: Message):
    await message.answer(strings['tba'])
    

@dp.message(lambda message: message.text == strings["back"])
async def handle_upload_button(message: Message):
    user_states[message.from_user.id] = 'main'
    await message.answer(
        strings['main'],
        reply_markup=get_main_keyboard()
    )
    
@dp.message(lambda message: user_states.get(message.from_user.id) == 'awaiting_pdf')
async def handle_upload_button(message: Message):
    if not message.document:
        #await message.reply(strings["request_pdf"])
        text = message.text
        words = text.split()
        if len(words) == 0:
            await message.answer(strings['noinput'])
            return
        elif len(words) == 1:
            file_name = f'{words[0].lower()}_{int(time.time())}.txt'
        else:
            file_name = f'{words[0].lower()}_{words[1].lower()}_{int(time.time())}.txt'
        destination = os.path.join(files_dir, str(message.chat.id), file_name)
        try:
            os.mkdir(os.path.join(files_dir, str(message.chat.id)))
        except:
            pass
        with open(os.path.join(destination), 'w', encoding='utf-8') as f:
            f.write(text)
        await message.reply(strings["success"])
        return
    try:
        pdf = message.document
        file_id = pdf.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file_name = pdf.file_name
        destination = os.path.join(files_dir, str(message.chat.id), file_name)
        if os.path.exists(destination):
            for i in range(1, 1025):
                dest = destination[:-4]+ f' ({i})' + destination[-4:]
                if not os.path.exists(dest):
                    destination = dest
                    break
        await bot.download_file(file_path, destination)
        
        await message.reply(strings['success'])
        user_states[message.from_user.id] = 'awaiting_pdf'
        
    except Exception as e:
        await message.reply(f"Error: {e}")

@dp.message()
async def default_run(message : Message):
    await message.answer(strings['pleasereset'])

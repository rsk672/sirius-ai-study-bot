import os
import PyPDF2
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from dotenv import load_dotenv

from aiogram.types import Message, FSInputFile

from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import time

from data.database import *
from rag.rag import *
from splitter.splitter import Splitter
from OCR.ocr import ImageToText

import re
from utils.logger import logger

db = Database()
rag = RAG()
splitter_instance = Splitter()
#databasa.py

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

files_dir = 'data/files'

strings = {'main' : 'Главная', 'load' : 'Загрузить', 'ask' : 'Спросить', 'back' : 'Главная',
           'hi' : 'Я суперпупермегаумный бот.', 'awaiting_pdf' : 'Отправьте PDF-файл или введите текст',
           'awaiting_query' : 'Пожалуйста, введите запрос', 'save' : 'Сохранить',
           'success' : 'Файл успешно сохранён. Хотите отправить еще?', 'noinput' : 'Отправьте непустое сообщение!',
           'pleasereset' : 'Пожалуйста, используйте команду /start.', 'tba' : 'Такой функции у нас пока нет((',
           'pleasewait' : 'Подождите, идёт обработка...', 'outoftokens' : 'Error: out of tokens'}

#Главная клавиатура - Загрузить и Спросить
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=strings["ask"], request_location=False))
    builder.add(KeyboardButton(text=strings["load"], request_location=False))
    #builder.add(KeyboardButton(text=strings["back"], request_location=False))
    builder.adjust(2, 1) 
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        #input_field_placeholder="Выберите действие..."
    )

#Клавиатура, когда пользователь отправляет пдф, сохранить или нет
def get_checkout_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=strings["save"], request_location=False))
    builder.add(KeyboardButton(text=strings["back"], request_location=False))
    builder.adjust(2, 1)
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        #input_field_placeholder="Выберите действие..."
    )

#Клавиатура, когда пользователь работает с чатом, только назад
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
        strings['awaiting_pdf'],
        reply_markup=get_empty_keyboard()
    )
    

@dp.message(lambda message: message.text == strings["ask"]) ### Ответ на вопрос
async def handle_upload_button(message: Message):
    user_states[message.from_user.id] = 'awaiting_query'
    await message.answer(
        strings['awaiting_query'],
        reply_markup = get_empty_keyboard()
    )
    
buffer = []

@dp.message(lambda message: message.text == strings["save"]) ### Сохранить
async def handle_upload_button(message: Message):
    for x in buffer:
        if x[0] == None:
            db.add(ListStrtoListData(*x[1]))
        else:
            destination = upload_to_database(*x[0])
            with open(os.path.join(destination), 'w', encoding='utf-8') as f:
                f.write(x[1])
    user_states[message.from_user.id] = 'main'
    await message.answer(
        strings['success'],
        reply_markup = get_main_keyboard()
    )
    

@dp.message(lambda message: message.text == strings["back"]) ### Домой
async def handle_upload_button(message: Message):
    user_states[message.from_user.id] = 'main'
    global buffer
    buffer = []
    await message.answer(
        strings['main'],
        reply_markup=get_main_keyboard()
    )

def find_file_location(chat_id:int, type:str)->list[str]:
    file_name = f'{int(time.time_ns())}.{type}'
    destination = os.path.join(files_dir, str(chat_id), file_name)
    try:
        os.mkdir(os.path.join(files_dir, str(chat_id)))
    except:
        pass
    ##for cause if dumb user sends two same files in the same second
    if os.path.exists(destination):
        for i in range(1, 1025):
            dest = destination[:-4]+ f' ({i})' + destination[-4:]
            if not os.path.exists(dest):
                destination = dest
                break
    return [destination, file_name]
def upload_to_database(texts:list[str], outer_file_name:str, chat_id:int, message_id:int, type:str):
    destination, file_name = find_file_location(chat_id, type)
    db.add(ListStrtoListData(texts, file_name, chat_id, message_id, outer_file_name))
    return destination

async def splitter(text:str)->list[str]:
    print(text)
    batches = (await splitter_instance.query(text)).batches
    print(batches)
    return batches

@dp.message(lambda message: user_states.get(message.from_user.id) == 'awaiting_pdf')
async def handle_upload_button(message: Message):
    try:
        if message.document:
            doc = message.document
            file_id = doc.file_id
            file_info = await bot.get_file(file_id)
            file_path = file_info.file_path
            file_name = doc.file_name
            
            file_ext = os.path.splitext(file_name)[1].lower()[1:]
            
            destination, inner_file_name = find_file_location(message.chat.id, file_ext)
            await bot.download_file(file_path, destination)
            
            full_text = ""
            if file_ext in ['pdf']:
                full_text = await PDFToText(destination)

            elif file_ext in ['jpg', 'jpeg', 'bmp', 'tiff', 'gif', 'png']:
                full_text = await ImageToText(destination)
            elif not full_text:
                try:
                    with open(destination, 'r', encoding='utf-8', errors='ignore') as file:
                        full_text = file.read()
                except:
                    pass
            if full_text:
                logger.info(f"Распознанный текст:\n{full_text}...")
                await message.reply(f"Распознанный текст:\n{full_text}...")
                db.add(ListStrtoListData(await splitter(full_text), inner_file_name,
                                        message.chat.id, message.message_id, file_name))
                await message.reply(strings['success'])
            else:
                await message.reply(f"Не удалось извлечь текст из файла формата {file_ext.upper()}")
            return
            
        if message.photo:
            photo = message.photo[-1]
            file_name = f"Photo_{int(time.time())}"
            file_ext = "jpg"
            path, inner_file_name = find_file_location(message.chat.id, file_ext)
            await bot.download(file=photo, destination=path)
            text = await ImageToText(path)
            logger.info(f"Распознанный текст:\n{text}...")
            await message.reply(f"Распознанный текст:\n{text}...")
            db.add(ListStrtoListData(await splitter(text), inner_file_name,
                                    message.chat.id, message.message_id, file_name))
            return
        text = message.text
        clean_text  = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s_]', '', text)
        words = clean_text.split()
        if len(words) == 0:
            await message.answer(strings['noinput'])
            return
        elif len(words) == 1:
            file_name = f'{words[0].lower()}.txt'
        else:
            file_name = f'{words[0].lower()}_{words[1].lower()}.txt'
        destination = upload_to_database(await splitter(text), file_name, message.chat.id, message.message_id, "txt")
        with open(os.path.join(destination), 'w', encoding='utf-8') as f:
            f.write(text)
        await message.reply(strings["success"])
        return

    except Exception as e:
            logger.error(f"Ошибка обработки файла: {str(e)}")
            await message.reply(f"Ошибка при обработке файла: {str(e)}")


@dp.message(lambda message: user_states.get(message.from_user.id) == 'awaiting_query')
async def handle_query_botton(message : Message):
    try:
        pleasewait = await message.answer(strings['pleasewait'])
        ans = await rag.query(message.text, message.chat.id)
        response = []
        for path in ans.paths:
            print(f"path={path}")
            if path != 'None':
                print(FSInputFile(os.path.join(files_dir, str(message.chat.id), path)))
                try:
                    await message.answer_document(document=FSInputFile(
                        os.path.join(files_dir, str(message.chat.id), path),
                        db.path_to_name(message.chat.id, path)))
                except Exception as e:
                    await message.reply(f"Error: {e}")
        await pleasewait.delete()
        await message.reply(
            ans.response,
            reply_markup=get_empty_keyboard()
        )
    except:
        await pleasewait.delete()
        await message.reply(
            strings['outoftokens'],
            reply_markup=get_main_keyboard()
        )


@dp.message()
async def default_run(message : Message):
    await message.answer(strings['pleasereset'])

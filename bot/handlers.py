import os
import PyPDF2
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup
from dotenv import load_dotenv

from aiogram.types import Message, FSInputFile

from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import time

from data.database import *
from rag.rag import *
from splitter.splitter import Splitter
from OCR.ocr import ImageToText
from utils.logger import logger

import re
from utils.logger import logger
from OCR.ocr import PDFToText
from name import Name

db = Database()
rag = RAG()
splitter_instance = Splitter()
#databasa.py

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

files_dir = 'data/files'


strings = Name({'main' : 'Главная', 'load' : 'Загрузить', 'ask' : 'Спросить', 'back' : 'Главная',
           'hi' : 'Привет! 👋 Я твой помощник для работы с конспектами.\n\n'
           'Загружай материалы, задавай вопросы по ним или управляй ими — всё в одном месте! Более подробно в /help 📚\n\n'\
           'Выбирай действие в меню ⬇️',
           'tutorial' : '✨ Доступные действия:\n\n'\
           '📤 Загрузить — Отправь мне текст, PDF-файл или фото. Я сохраню это как конспект для вопросов.\n\n'\
           '💬 Спросить — Перейди в режим чата, чтобы задавать вопросы по всем загруженным материалам. Я найду ответы в твоих конспектах!\n\n'\
           '🗑 Удалить — Хочешь удалить конкретный конспект? Ответь (reply) на сообщение с ним этой командой, и я его забуду.\n\n'\
           'Готов помочь с учебой! 🚀',
           'awaiting_pdf' : 'Отправьте PDF, фото или введите текст',
           'awaiting_query' : 'Пожалуйста, введите запрос', 'save' : 'Сохранить',
           'success' : 'Файл успешно сохранён. Хотите отправить еще?', 'noinput' : 'Отправьте непустое сообщение!',
           'pleasereset' : 'Пожалуйста, используйте команду /start.', 'tba' : 'Такой функции у нас пока нет',
           'pleasewait' : 'Подождите, идёт обработка...', 'outoftokens' : 'Out of tokens',
           'delete': 'Удалить', 'awaiting_deletion':"Ответьте на сообщение с конспектом, которое вы хотите удалить.",
           'deleted': 'Файл успешно удалён', 'nothing_to_delete': 'Невозможно удалить т.к. нечего удалять', 
           'no' : 'Нет', 'yes' : 'Да', 'OK' : 'Хорошо', 'smthwentwrong' : 'Что-то пошло не так',
           'filenotsupport' : 'Неподдерживаемый формат файла: {0}', 'emptyfile' : 'Не удалось извлечь текст из файла'
           })

#Главная клавиатура - Загрузить и Спросить
def get_main_keyboard():
    
    keyhoard = [[KeyboardButton(text=strings["ask"]), 
                 KeyboardButton(text=strings["load"])],
                [KeyboardButton(text=strings["delete"])]]
    #builder.add(KeyboardButton(text=strings["back"], request_location=False))
    return ReplyKeyboardMarkup(keyboard=keyhoard)

#Клавиатура, когда пользователь отправляет пдф, сохранить или нет
def get_checkout_keyboard():
    keyhoard = [[KeyboardButton(text=strings["save"]), 
                 KeyboardButton(text=strings["back"])]]
    return ReplyKeyboardMarkup(keyboard=keyhoard)

#Клавиатура, когда пользователь работает с чатом, только назад
def get_empty_keyboard():
    keyhoard = [[KeyboardButton(text=strings["back"])]]
    return ReplyKeyboardMarkup(keyboard=keyhoard)

user_states = {}
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        strings["hi"],
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("help"))
async def cmd_start(message: Message):
    await message.answer(strings["tutorial"])


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

@dp.message(lambda message: message.text == strings["delete"]) ### Ответ на вопрос
async def handle_delete_button(message: Message):
    user_states[message.from_user.id] = 'awaiting_deletion'
    await message.answer(
        strings['awaiting_deletion'],
        reply_markup = get_empty_keyboard()
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
        pleasewait = await message.answer(strings['pleasewait'])
        if message.document:
            doc = message.document
            file_id = doc.file_id
            file_info = await bot.get_file(file_id)
            file_path = file_info.file_path
            file_name = doc.file_name
            
            file_ext = os.path.splitext(file_name)[1].lower()[1:]
            
            destination, inner_file_name = find_file_location(message.chat.id, file_ext)
            await bot.download_file(file_path, destination)
            logger.info(f'{file_ext=}')
            
            full_text = ""
            if file_ext in ['pdf']:
                full_text = await PDFToText(destination)
                print('PDFTpText\n\n\n\n\n', full_text)

                logger.info(f'OCR ENDED {full_text=}')

            elif file_ext in ['jpg', 'jpeg', 'bmp', 'tiff', 'png']:
                full_text = await ImageToText(destination)
            elif file_ext in ['txt']:
                try:
                    with open(destination, 'r', encoding='utf-8', errors='ignore') as file:
                        full_text = file.read()
                except:
                    pass
            else:
                await message.reply(strings['filenotsupport', file_ext.upper()])
                return
            if full_text:
                logger.info(f"Распознанный текст:\n{full_text}...")
                #await message.reply(f"Распознанный текст:\n{full_text}...")
                #buffer.append((None, [await splitter(full_text), inner_file_name,
                #                      message.chat.id, message.message_id, file_name]))
                db.add(ListStrtoListData(await splitter(full_text), inner_file_name,
                                      message.chat.id, message.message_id, file_name))
            else:
                await message.reply(strings['emptyfile'])
                return
            
        elif message.photo:
            photo = message.photo[-1]
            file_name = f"Photo_{int(time.time())}"
            file_ext = "png"
            path, inner_file_name = find_file_location(message.chat.id, file_ext)
            await bot.download(file=photo, destination=path)
            text = await ImageToText(path)
            logger.info(f"Распознанный текст:\n{text}...")
            #buffer.append((None, [await splitter(text), inner_file_name,
            #                          message.chat.id, message.message_id, file_name]))
            db.add(ListStrtoListData(await splitter(text), inner_file_name,
                                    message.chat.id, message.message_id, file_name))
        else:
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
            #buffer.append(([await splitter(text), file_name, message.chat.id, message.message_id, "txt"], text))
            destination = upload_to_database(await splitter(text), file_name, message.chat.id, message.message_id, "txt")
            with open(os.path.join(destination), 'w', encoding='utf-8') as f:
                f.write(text)

            
        #await message.reply(str(buffer[-1][1][0])[:4000], reply_markup = get_checkout_keyboard())
        #user_states[message.from_user.id] = 'checkout'
        await message.reply(strings['success'], reply_markup = get_main_keyboard())
        user_states[message.from_user.id] = 'checkout'
        await pleasewait.delete()
            

    except Exception as e:
            logger.error(f"Ошибка обработки файла: {str(e)}")
            await message.reply(strings['smthwentwrong'], reply_markup = get_main_keyboard())
            user_states[message.from_user.id] = 'checkout'
            await pleasewait.delete()
            


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
                    print(f"Error: {e}")
                    await message.reply(strings['smthwentwrong'])
        await pleasewait.delete()
        await message.reply(
            ans.response,
            reply_markup=get_empty_keyboard()
        )
    except:
        await pleasewait.delete()
        print(f"Error: {strings['outoftokens']}")
        await message.reply(
            strings['smthwentwrong'],
            reply_markup=get_main_keyboard()
        )


@dp.message(lambda message: (user_states.get(message.from_user.id) == 'awaiting_deletion') and message.reply_to_message)
async def handle(message : Message):
    try:
        paths = db.remove(message.reply_to_message.message_id, message.chat.id)
        if len(paths) == 0:
            await message.reply(strings['nothing_to_delete'])
            return
        for path in paths:
            os.remove(os.path.join(files_dir, str(message.chat.id), path))
        await message.reply_to_message.reply(strings['deleted'], reply_markup=get_main_keyboard())
        await bot.set_message_reaction(message.chat.id, message.reply_to_message.message_id, reaction=[{"type": "emoji", "emoji": "🔥"}], is_big=True)
    except Exception as e:
        print(f"Error: {e}")
        await message.reply(strings['smthwentwrong'])
        
@dp.message()
async def default_run(message : Message):
    await message.answer(strings['pleasereset'])

import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, FSInputFile, KeyboardButton

from data.database import Database, ListStrtoListData
from rag.rag import RAG
from splitter.splitter import Splitter
from ocr.ocr import ImageToText, PDFToText
from utils.logger import logger
from name import Name

load_dotenv()

db = Database()
rag = RAG()
splitter_instance = Splitter()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in env/.env")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

FILES_DIR = Path("data/files")

strings = Name({
    "main": "Главная",
    "load": "Загрузить",
    "ask": "Спросить",
    "back": "Главная",
    "hi": "Привет! 👋 Я твой помощник для работы с конспектами.\n\n"
          "Загружай материалы, задавай вопросы по ним или управляй ими — всё в одном месте! Более подробно в /help 📚\n\n"
          "Выбирай действие в меню ⬇️",
    "tutorial": "✨ Доступные действия:\n\n"
                "📤 Загрузить — Отправь мне текст, PDF-файл или фото. Я сохраню это как конспект для вопросов.\n\n"
                "💬 Спросить — Перейди в режим чата, чтобы задавать вопросы по всем загруженным материалам. Я найду ответы в твоих конспектах!\n\n"
                "🗑 Удалить — Хочешь удалить конкретный конспект? Ответь (reply) на сообщение с ним этой командой, и я его забуду.\n\n"
                "Готов помочь с учебой! 🚀",
    "awaiting_pdf": "Отправьте PDF, фото или введите текст",
    "awaiting_query": "Пожалуйста, введите запрос",
    "save": "Сохранить",
    "success": "Файл успешно сохранён. Хотите отправить еще?",
    "noinput": "Отправьте непустое сообщение!",
    "pleasereset": "Пожалуйста, используйте команду /start.",
    "pleasewait": "Подождите, идёт обработка...",
    "outoftokens": "Out of tokens",
    "delete": "Удалить",
    "awaiting_deletion": "Ответьте на сообщение с конспектом, которое вы хотите удалить.",
    "deleted": "Файл успешно удалён",
    "nothing_to_delete": "Невозможно удалить т.к. нечего удалять",
    "smthwentwrong": "Что-то пошло не так",
    "filenotsupport": "Неподдерживаемый формат файла: {0}",
    "emptyfile": "Не удалось извлечь текст из файла",
})


def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=strings["ask"]), KeyboardButton(text=strings["load"])],
        [KeyboardButton(text=strings["delete"])],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard)


def get_empty_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=strings["back"])]])


user_states: dict[int, str] = {}
buffer = []  # оставляю, чтобы поведение не ломать (хотя сейчас не используется)


def ensure_chat_dir(chat_id: int) -> Path:
    chat_dir = FILES_DIR / str(chat_id)
    chat_dir.mkdir(parents=True, exist_ok=True)
    return chat_dir


def find_file_location(chat_id: int, ext: str) -> tuple[Path, str]:
    chat_dir = ensure_chat_dir(chat_id)

    file_name = f"{time.time_ns()}.{ext}"
    dest = chat_dir / file_name

    if dest.exists():
        stem = dest.stem
        suffix = dest.suffix
        for i in range(1, 1025):
            candidate = chat_dir / f"{stem} ({i}){suffix}"
            if not candidate.exists():
                dest = candidate
                file_name = candidate.name
                break

    return dest, file_name


async def split_text(text: str) -> list[str]:
    batches = await splitter_instance.query(text)
    return batches


def sanitize_text_filename(text: str) -> str:
    clean = re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9\s_]", "", text or "").strip()
    words = clean.split()
    if not words:
        return ""
    if len(words) == 1:
        return f"{words[0].lower()}.txt"
    return f"{words[0].lower()}_{words[1].lower()}.txt"


def dedupe_paths(paths: list) -> list[str]:
    seen = set()
    out: list[str] = []
    for p in paths or []:
        p = str(p).strip()
        if not p or p.lower() == "none":
            continue

        # нормализация на случай "Path: xxx" или полного пути
        if p.lower().startswith("path:"):
            p = p.split(":", 1)[1].strip()
        p = p.strip("`\"' ")
        p = os.path.basename(p)

        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_states[message.from_user.id] = "main"
    await message.answer(strings["hi"], reply_markup=get_main_keyboard())


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(strings["tutorial"])


@dp.message(lambda message: message.text == strings["load"])
async def handle_load_button(message: Message):
    user_states[message.from_user.id] = "awaiting_pdf"
    await message.answer(strings["awaiting_pdf"], reply_markup=get_empty_keyboard())


@dp.message(lambda message: message.text == strings["ask"])
async def handle_ask_button(message: Message):
    user_states[message.from_user.id] = "awaiting_query"
    await message.answer(strings["awaiting_query"], reply_markup=get_empty_keyboard())


@dp.message(lambda message: message.text == strings["back"])
async def handle_back_button(message: Message):
    user_states[message.from_user.id] = "main"
    global buffer
    buffer = []
    await message.answer(strings["main"], reply_markup=get_main_keyboard())


@dp.message(lambda message: message.text == strings["delete"])
async def handle_delete_button(message: Message):
    user_states[message.from_user.id] = "awaiting_deletion"
    await message.answer(strings["awaiting_deletion"], reply_markup=get_empty_keyboard())


@dp.message(lambda message: user_states.get(message.from_user.id) == "awaiting_pdf")
async def handle_upload(message: Message):
    pleasewait = await message.answer(strings["pleasewait"])
    try:
        if message.document:
            doc = message.document
            file_info = await bot.get_file(doc.file_id)
            file_name = doc.file_name or "document"

            ext = os.path.splitext(file_name)[1].lower().lstrip(".")
            dest, inner_file_name = find_file_location(message.chat.id, ext)
            await bot.download_file(file_info.file_path, str(dest))

            if ext == "pdf":
                full_text = await PDFToText(str(dest))
                logger.info(f'{full_text=}')
            elif ext in {"jpg", "jpeg", "bmp", "tiff", "png"}:
                full_text = await ImageToText(str(dest))
            elif ext == "txt":
                with open(dest, "r", encoding="utf-8", errors="ignore") as f:
                    full_text = f.read()
            else:
                await message.reply(strings["filenotsupport"].format(ext.upper()))
                return

            if not full_text or not full_text.strip():
                await message.reply(strings["emptyfile"])
                return

            db.add(ListStrtoListData(
                await split_text(full_text),
                inner_file_name,
                message.chat.id,
                message.message_id,
                file_name,
            ))

            await message.reply(strings["success"], reply_markup=get_main_keyboard())
            user_states[message.from_user.id] = "checkout"
            return

        if message.photo:
            photo = message.photo[-1]
            file_name = f"Photo_{int(time.time())}"
            ext = "png"

            dest, inner_file_name = find_file_location(message.chat.id, ext)
            await bot.download(file=photo, destination=str(dest))

            text = await ImageToText(str(dest))
            if not text or not text.strip():
                await message.reply(strings["emptyfile"])
                return

            db.add(ListStrtoListData(
                await split_text(text),
                inner_file_name,
                message.chat.id,
                message.message_id,
                file_name,
            ))

            await message.reply(strings["success"], reply_markup=get_main_keyboard())
            user_states[message.from_user.id] = "checkout"
            return

        # plain text
        text = message.text or ""
        file_name = sanitize_text_filename(text)
        if not file_name:
            await message.answer(strings["noinput"])
            return

        dest, inner_file_name = find_file_location(message.chat.id, "txt")
        with open(dest, "w", encoding="utf-8") as f:
            f.write(text)

        db.add(ListStrtoListData(
            await split_text(text),
            inner_file_name,
            message.chat.id,
            message.message_id,
            file_name,
        ))

        await message.reply(strings["success"], reply_markup=get_main_keyboard())
        user_states[message.from_user.id] = "checkout"

    except Exception:
        logger.exception("Ошибка обработки файла")
        await message.reply(strings["smthwentwrong"], reply_markup=get_main_keyboard())
        user_states[message.from_user.id] = "checkout"
    finally:
        try:
            await pleasewait.delete()
        except Exception:
            pass


@dp.message(lambda message: user_states.get(message.from_user.id) == "awaiting_query")
async def handle_query(message: Message):
    pleasewait = await message.answer(strings["pleasewait"])
    try:
        ans = await rag.query(message.text, message.chat.id)
        paths = dedupe_paths(getattr(ans, "paths", []))

        for path in paths:
            try:
                full_path = FILES_DIR / str(message.chat.id) / path
                await message.answer_document(
                    document=FSInputFile(str(full_path), db.path_to_name(message.chat.id, path))
                )
            except Exception:
                logger.exception("Не удалось отправить файл-источник")
                await message.reply(strings["smthwentwrong"])

        filtered = str(getattr(ans, "response", "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        await message.reply(filtered, reply_markup=get_empty_keyboard())

    except Exception:
        logger.exception("Ошибка обработки запроса")
        await message.reply(strings["smthwentwrong"], reply_markup=get_main_keyboard())
    finally:
        try:
            await pleasewait.delete()
        except Exception:
            pass


@dp.message(lambda message: (user_states.get(message.from_user.id) == "awaiting_deletion") and message.reply_to_message)
async def handle_delete(message: Message):
    try:
        paths = db.remove(message.reply_to_message.message_id, message.chat.id)
        if not paths:
            await message.reply(strings["nothing_to_delete"])
            return

        for p in paths:
            try:
                (FILES_DIR / str(message.chat.id) / p).unlink(missing_ok=True)
            except Exception:
                logger.exception("Не удалось удалить файл с диска")

        await message.reply_to_message.reply(strings["deleted"], reply_markup=get_main_keyboard())

        try:
            await bot.set_message_reaction(
                message.chat.id,
                message.reply_to_message.message_id,
                reaction=[{"type": "emoji", "emoji": "🔥"}],
                is_big=True,
            )
        except Exception:
            pass

    except Exception:
        logger.exception("Ошибка удаления")
        await message.reply(strings["smthwentwrong"])


@dp.message()
async def default_run(message: Message):
    await message.answer(strings["pleasereset"])

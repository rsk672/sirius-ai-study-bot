from __future__ import annotations

import os
import re
import base64
import mimetypes
from pathlib import Path
from typing import Optional

import httpx
import fitz

from utils.config import (
    OCR_OPENROUTER_URL,
    OCR_VL_MODEL,
    OCR_PROMPT_PATH,
    OCR_LANGUAGE_HINT,
    OCR_TIMEOUT,
    OCR_MAX_TOKENS,
)

PROMPT_PATH = Path(OCR_PROMPT_PATH)

_PROMPT_CACHE: Optional[str] = None
_HTTP_CLIENT: Optional[httpx.AsyncClient] = None


def get_api_key() -> str:
    key = os.getenv("LLM_KEY")
    if not key:
        raise RuntimeError("LLM_KEY is missing in environment (.env)")
    return key


def openrouter_headers(api_key: str) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    site = os.getenv("OPENROUTER_SITE_URL")
    title = os.getenv("OPENROUTER_APP_NAME")
    if site:
        headers["HTTP-Referer"] = site
    if title:
        headers["X-Title"] = title
    return headers


def get_http_client(timeout: float = OCR_TIMEOUT) -> httpx.AsyncClient:
    """
    Singleton AsyncClient для переиспользования соединений.
    """
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None:
        _HTTP_CLIENT = httpx.AsyncClient(timeout=timeout, http2=True)
    else:
        _HTTP_CLIENT.timeout = httpx.Timeout(timeout)
    return _HTTP_CLIENT


async def close_http_client() -> None:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is not None:
        await _HTTP_CLIENT.aclose()
        _HTTP_CLIENT = None


def load_prompt() -> str:
    global _PROMPT_CACHE
    if _PROMPT_CACHE is not None:
        return _PROMPT_CACHE

    if not PROMPT_PATH.exists():
        raise RuntimeError(f"OCR prompt file not found: {PROMPT_PATH}")

    _PROMPT_CACHE = PROMPT_PATH.read_text(encoding="utf-8")
    return _PROMPT_CACHE


def render_prompt(language_hint: str = OCR_LANGUAGE_HINT) -> str:
    template = load_prompt()
    try:
        return template.format(language_hint=language_hint)
    except KeyError:
        return template


def encode_file_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def guess_mime(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def data_url_from_path(path: str) -> str:
    mime = guess_mime(path)
    b64 = encode_file_b64(path)
    return f"data:{mime};base64,{b64}"


def pixmap_to_png_data_url(pix: fitz.Pixmap) -> str:
    png_bytes = pix.tobytes("png")
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def is_text_layer_usable(
    text: str,
    *,
    min_len: int,
    min_cyr_ratio: float = 0.12,
) -> bool:
    """
    Эвристика: если text-layer похож на настоящий русский текст — используем его,
    иначе считаем мусором и делаем OCR (Qwen).

    min_cyr_ratio — минимальная доля кириллицы среди буквенных символов.
    """
    if not text:
        return False

    text = text.strip()
    if len(text) < min_len:
        return False

    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return False

    cyr = [ch for ch in letters if ("А" <= ch <= "я") or ch in "Ёё"]
    return (len(cyr) / len(letters)) >= min_cyr_ratio


async def qwen_ocr_image_data_url(
    image_data_url: str,
    *,
    model: str = OCR_VL_MODEL,
    language_hint: str = OCR_LANGUAGE_HINT,
    timeout: float = OCR_TIMEOUT,
    max_tokens: int = OCR_MAX_TOKENS,
) -> str:
    api_key = get_api_key()
    prompt = render_prompt(language_hint)

    payload = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }
        ],
    }

    client = get_http_client(timeout=timeout)
    r = await client.post(
        OCR_OPENROUTER_URL,
        headers=openrouter_headers(api_key),
        json=payload,
    )
    r.raise_for_status()
    data = r.json()

    content = data["choices"][0]["message"]["content"]
    return clean_text(content)

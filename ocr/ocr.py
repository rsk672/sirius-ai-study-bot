from __future__ import annotations

import asyncio
from typing import Optional, List, Tuple

import fitz

from utils.config import OCR_PDF_DPI, OCR_MIN_TEXT_CHARS_PER_PAGE
from utils.logger import logger

from .helpers import (
    data_url_from_path,
    pixmap_to_png_data_url,
    qwen_ocr_image_data_url,
    is_text_layer_usable,
)


async def ImageToText(path: str) -> str:
    """
    OCR одиночного изображения через Qwen-VL (OpenRouter).
    """
    image_data_url = data_url_from_path(path)
    text = await qwen_ocr_image_data_url(image_data_url)
    return text.replace("<unk>", "")


async def PDFToText(
    path: str,
    *,
    dpi: int = OCR_PDF_DPI,
    min_text_chars_per_page: int = OCR_MIN_TEXT_CHARS_PER_PAGE,
    max_pages: Optional[int] = None,
    concurrency: int = 4,
) -> str:
    """
    Умный OCR PDF:
      - если text-layer страницы выглядит нормальным -> берём его
      - иначе -> OCR через Qwen
    OCR страниц выполняется параллельно с лимитом `concurrency`.
    """
    doc = fitz.open(path)
    try:
        page_count = doc.page_count
        if max_pages is not None:
            page_count = min(page_count, max_pages)

        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        # prepared: (page_index, mode, payload)
        # mode: "text" -> payload is text_layer
        # mode: "ocr"  -> payload is image_data_url
        prepared: List[Tuple[int, str, str]] = []

        for i in range(page_count):
            page = doc.load_page(i)
            text_layer = (page.get_text("text") or "").strip()

            if is_text_layer_usable(text_layer, min_len=min_text_chars_per_page):
                prepared.append((i, "text", text_layer))
                continue

            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_url = pixmap_to_png_data_url(pix)
            prepared.append((i, "ocr", img_url))

        sem = asyncio.Semaphore(max(1, concurrency))
        results: List[str] = [""] * page_count

        async def ocr_one(page_index: int, img_url: str) -> None:
            async with sem:
                logger.info("OCR page %s via Qwen", page_index + 1)
                results[page_index] = await qwen_ocr_image_data_url(img_url)

        tasks: List[asyncio.Task] = []
        for i, mode, payload in prepared:
            if mode == "text":
                results[i] = payload
            else:
                tasks.append(asyncio.create_task(ocr_one(i, payload)))

        if tasks:
            await asyncio.gather(*tasks)

        parts: List[str] = []
        for i in range(page_count):
            parts.append(f"--- PAGE {i+1} ---\n{results[i].strip()}".strip())

        return "\n\n".join(parts).strip()

    finally:
        doc.close()

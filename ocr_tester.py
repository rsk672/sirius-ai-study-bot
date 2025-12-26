from OCR.ocr import ImageToText
from splitter.splitter import Splitter
import asyncio
spl = Splitter()
print(*(asyncio.run(spl.query(asyncio.run(ImageToText("OCR/image.png"))))))
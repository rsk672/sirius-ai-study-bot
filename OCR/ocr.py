# Импортируйте библиотеку для кодирования в Base64
import base64
import httpx
import json
import os
import asyncio
# Создайте функцию, которая кодирует файл и возвращает результат.
def encode_file(file_path):
  with open(file_path, "rb") as fid:
    file_content = fid.read()
  return base64.b64encode(file_content).decode("utf-8")

async def PDFToText(path:str)->str:
    AUTH_KEY = os.getenv("AUTH_KEY")
    FOLDER_ID = os.getenv("FOLDER_ID")
    client = httpx.AsyncClient()
    data = {"mimeType": "application/pdf",
            "languageCodes": ["ru","en"],
            "model": "handwritten",
            "content": encode_file(path)}

    url = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"

    headers= {"Content-Type": "application/json",
            "Authorization": "Bearer {:s}".format(AUTH_KEY),
            "x-folder-id": FOLDER_ID,
            "x-data-logging-enabled": "true"}
    
    resp = await client.post(url, headers=headers, data=json.dumps(data))
    print(resp.json())
    return resp.json()["result"]["textAnnotation"]["fullText"]

async def ImageToText(path:str)->str:
    AUTH_KEY = os.getenv("AUTH_KEY")
    FOLDER_ID = os.getenv("FOLDER_ID")
    client = httpx.AsyncClient()
    data = {"mimeType": "image",
            "languageCodes": ["ru","en"],
            "model": "handwritten",
            "content": encode_file(path)}

    url = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"

    headers= {"Content-Type": "application/json",
            "Authorization": "Bearer {:s}".format(AUTH_KEY),
            "x-folder-id": FOLDER_ID,
            "x-data-logging-enabled": "true"}
    
    resp = await client.post(url, headers=headers, data=json.dumps(data))
    return resp.json()["result"]["textAnnotation"]["fullText"].replace('<unk>', '')
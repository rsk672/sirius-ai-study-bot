import os
import asyncio
from dotenv import load_dotenv
from dataclasses import dataclass
import httpx
import json
import openai
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    batches:list[str] # all of the batches from the text
class Splitter:
    def __init__(self):
        load_dotenv()
        self.YC_FOLDER_ID = os.getenv("YC_FOLDER_ID")
        self.YC_API_KEY = os.getenv("YC_API_KEY")
        self.YC_MODEL = "yandexgpt/rc"
        self.client = openai.AsyncOpenAI(
            api_key=self.YC_API_KEY,
            base_url="https://llm.api.cloud.yandex.net/v1",
            project=self.YC_FOLDER_ID,
        )
        with open("splitter/splitter_prompt.txt", encoding="utf-8") as q:
            self.PROMPT = q.read()
    
    async def query(self, text:str)->ResponseFormat:
        response = await self.client.chat.completions.create(
            model=f"gpt://{self.YC_FOLDER_ID}/{self.YC_MODEL}",
            messages=[
                    {"role": "system",
                     "content": self.PROMPT},
                    {"role": "user", "content": text}
                ],
            max_tokens=2048, 
            temperature=0.3,
            stream=False,
        )
        return list(response.choices[0].message.content.split("\n\n\n"))
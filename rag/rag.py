from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional, List

import httpx
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain.agents.structured_output import ToolStrategy
from langgraph.checkpoint.memory import InMemorySaver

from data import database as db
from proxy_getter.find_proxies import ProxyGetter
from utils.config import (
    RAG_MODEL_NAME,
    RAG_BASE_URL,
    RAG_TEMPERATURE,
    RAG_MAX_TOKENS,
    RAG_PROMPT_PATH,
    RAG_HTTP_TIMEOUT,
    RAG_EMPTY_RETRIEVAL_TEXT,
    RAG_DEFAULT_LABEL,
)


@dataclass
class ResponseFormat:
    response: str
    paths: List[str]


class RAG:
    def __init__(
        self,
        model_name: str = RAG_MODEL_NAME,
        base_url: str = RAG_BASE_URL,
        temperature: float = RAG_TEMPERATURE,
        max_tokens: int = RAG_MAX_TOKENS,
        prompt_path: str = RAG_PROMPT_PATH,
    ):
        load_dotenv()

        api_key = os.getenv("LLM_KEY")
        if not api_key:
            raise RuntimeError("LLM_KEY is missing in env/.env")

        proxy = ProxyGetter().get()
        http_client = (
            httpx.Client(proxy=proxy, timeout=RAG_HTTP_TIMEOUT)
            if proxy
            else httpx.Client(timeout=RAG_HTTP_TIMEOUT)
        )

        self.model = ChatOpenAI(
            model=model_name,
            openai_api_base=base_url,   # оставляю как у вас (под вашу версию langchain_openai)
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            client=http_client,
        )

        self.prompt = self._load_prompt(prompt_path)
        print(self.prompt, file=sys.stderr)

        self.database = db.Database()
        self.checkpointer = InMemorySaver()

    @staticmethod
    def _load_prompt(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _make_tools(self, chat_id: int, label: Optional[str]) -> list:
        label_value = label if label is not None else RAG_DEFAULT_LABEL

        @tool
        def find_lecture_notes(text: str) -> str:
            """Find relevant conspekt fragments in the user's database."""
            datas = self.database.get(text=text, chat_id=chat_id, label=label_value)
            if not datas:
                return RAG_EMPTY_RETRIEVAL_TEXT

            return "\n\n".join(
                f"Path: {d.path}\nContent: {d.text}"
                for d in datas
            )

        return [find_lecture_notes]

    def _build_agent(self, chat_id: int, label: Optional[str]):
        tools = self._make_tools(chat_id, label)
        return create_agent(
            model=self.model,
            system_prompt=self.prompt,
            tools=tools,
            response_format=ToolStrategy(ResponseFormat),
            checkpointer=self.checkpointer,
        )

    async def query(self, text: str, chat_id: int, label: Optional[str] = None) -> ResponseFormat:
        agent = self._build_agent(chat_id, label)

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": text}]},
            {"configurable": {"thread_id": str(chat_id)}},
        )

        return result["structured_response"]

from langchain.agents import create_agent
from data import database as db
import os, sys
from dotenv import load_dotenv
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy
from langgraph.checkpoint.memory import InMemorySaver
from proxy_getter.find_proxies import ProxyGetter
import httpx
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    response:str
    paths:list[str]

class RAG:
    def __init__(self):
        load_dotenv()
        API_KEY = os.getenv("LLM_KEY")
        pg = ProxyGetter()
        self.model = ChatOpenAI(
            model="nex-agi/deepseek-v3.1-nex-n1:free",  # OpenRouter model ID #"nex-agi/deepseek-v3.1-nex-n1:free" "mistralai/devstral-2512:free"
            openai_api_base="https://openrouter.ai/api/v1",  # OpenRouter endpoint
            temperature=0.3,
            max_tokens=512,
            api_key=API_KEY,
            client = httpx.Client(proxy=pg.get())
        )
        with open('rag/prompt.txt', 'r') as f:
            self.prompt = f.read()
            print(self.prompt, file = sys.stderr)
        self.database = db.Database()
        self.checkpointer = InMemorySaver()

    def gen_tools(self, chat_id:int, label:str) -> list:
        @tool
        def find_conspekts(text:str)->str:
            """Query the database to find matching conspekts,
            
            Args:
                text: the text to which it'll find the most similiar conspekts from the database"""
            datas = self.database.get(text=text, chat_id=chat_id, label=label)
            serialized = "\n\n".join(
                (f"Path: {data.path}\nContent: {data.text}") for data in datas
            )
            print(serialized)
            return serialized
        return [find_conspekts]

    async def query(self, text:str, chat_id:int, label:str=None):
        tools = self.gen_tools(chat_id, label)
        self.agent = create_agent(
                model=self.model,
                system_prompt=self.prompt,
                tools=tools,
                response_format=ToolStrategy(ResponseFormat),
                checkpointer=self.checkpointer,
            )
        response = await self.agent.ainvoke({"messages": [{"role": "user", "content": text}]},
                                            {"configurable": {"thread_id": str(chat_id)}})
        return response['structured_response']

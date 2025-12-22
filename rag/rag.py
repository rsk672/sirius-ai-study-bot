from langchain.agents import create_agent
from data import database as db
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    response:str
    paths:list[str]
class RAG:
    def __init__(self):
        load_dotenv()
        API_KEY = os.getenv("LLM_KEY")
        self.model = ChatOpenAI(
            model="nex-agi/deepseek-v3.1-nex-n1:free",  # OpenRouter model ID #"nex-agi/deepseek-v3.1-nex-n1:free" "mistralai/devstral-2512:free"
            openai_api_base="https://openrouter.ai/api/v1",  # OpenRouter endpoint
            temperature=0.3,
            max_tokens=512,
            api_key=API_KEY
        )
        
        self.agent = create_agent(
            model=self.model,
            system_prompt=
            response_format=ToolStrategy(ResponseFormat),
        )
        self.database = db.Database()
    
    def query(self, text:str, chat_id:int, label:str=None):
        #2 step RAG
        #можно потом сделать более сложную архитектуру
        datas = self.database.get(text=text, chat_id=chat_id, label=label)
        serialized = "\n\n".join(
            (f"Path: {data.path}\nContent: {data.text}") for data in datas
        )
        response = self.agent.invoke({"messages": [{"role": "user", "content": text + "\n\n" + serialized}]})
        print(text + "\n\n" + serialized)
        return response['structured_response']
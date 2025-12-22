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
    batches:list[str] # all of the batches from the text
class Splitter:
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
            system_prompt="Your job is to split the text into batches, " \
            "such that an embedding of each batch would carry useful information," \
            " while keeping the size of each batch as big as possible." \
            "You are a proffesional." \
            "The entirety of the text should be within the batches," \
            " but batches can overlap minorly to allow for better results of the embedding.",
            response_format=ToolStrategy(ResponseFormat),
        )
    
    def query(self, text:str)->ResponseFormat:
        response = self.agent.invoke({"messages": [{"role": "user", "content": text}]})
        return response['structured_response']
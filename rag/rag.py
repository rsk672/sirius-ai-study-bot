from langchain.agents import create_agent
from data import database as db
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    response:str
    paths:list[str]
    ratings:list[float]



class RAG:
    def __init__(self):
        load_dotenv()
        API_KEY = os.getenv("LLM_KEY")
        self.model = ChatOpenAI(
            model="nex-agi/deepseek-v3.1-nex-n1:free",  # OpenRouter model ID
            openai_api_key=API_KEY,  # Your OpenRouter API key
            openai_api_base="https://openrouter.ai/api/v1",  # OpenRouter endpoint
            temperature=0.3,
            max_tokens=2048
        )
        self.agent = create_agent(
            model=self.model,
            tools=[self.get_relevant_conspect],
            system_prompt="You are a helpful assistant, " \
            "the user has submited some conspects on various topic. Provide information on the topics that the user has asked," \
            "you have a tool called get_relevant_conspect that will provide you with the path to the most relevant conspects as well as their contents," \
            " at the beggining of the file the user id and the label you'll need for the tool will be provided." \
            "In your response always rely on the conspects for information." \
            "After your response write the paths to the conspects you used for answering the user's question." \
            "Don't repeat the same path twice, if the information in the file wasn't used, don't print out its path." \
            "Only write a path if you think the user would need to see that file to understand the explanation." \
            "You can make derivations based on the conspects and also to use your own knowledge," \
            " but ALWAYS and i do mean ALWAYS specify when you are doing so." \
            "If no conspects were referenced then in the paths write 'None'." \
            "After your response write a float from 0 to 1 that is related to how much each conspect was used," \
            " each number should corespond to the path written previously.",
            response_format=ToolStrategy(ResponseFormat)
        )
        self.database = db.Database()
    
    @tool
    def get_relevant_conspect(self, user_input:str, chat_id:int, label:str='None')->str:
        """Finds the relevant conspect to a user input"""
        print(user_input, chat_id, label)
        datas = self.database.get(text=user_input, chat_id=chat_id, label=label)
        output = "\n\n".join(
            (f"Path: {data.path}\nContent: {data.text}") for data in datas
        )
        return output

    def query(self, text:str, chat_id:int, label:str='None'):
        #agenic RAG
        print("start")
        response = self.agent.invoke({"messages": 
                    [{"role": "user", "content": f"chat_id:{chat_id}, label:{label}\n\n{text}"}]})
        return response['structured_response']
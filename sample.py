

from langchain_groq import ChatGroq
from src.config import *

# llm_ = ChatGroq(model="qwen/qwen3-32b", api_key=api_key,temperature=0).profile
print(llm.profile)
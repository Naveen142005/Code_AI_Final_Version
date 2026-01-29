import json
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import llm
from src._agents.state import AgentState

class Router:

    
    def __init__(self):
        pass

    def route(self, query: str) -> str:
        
        system_prompt = """You are a Senior Technical Router. 
Classify the user query into ONE of three categories:

1. **CODE**: The user is asking about a specific class, function, variable, or logic block.
   - Keywords: "explain function", "how does the grader work", "what is vector store", "show me code for X"


3. **CHAT**: General conversation or greetings.
   - Keywords: "hi", "thanks", "hello", "goodbye"

Output ONLY the category name: "CODE", "OVERVIEW", or "CHAT".
"""

        try:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Query: {query}")
            ])
            
            content = response.content.strip().upper()
            
            # Robust extraction
            print('-'*40)
            print (content)
          
            if "CODE" in content: return "CODE"
            if "CHAT" in content: return "CHAT"
            
            return "CHAT"

        except Exception as e:
            print(f"[Router] => Error: {e}. Defaulting to CHAT.")
            return "CHAT"

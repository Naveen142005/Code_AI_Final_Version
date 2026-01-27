from langchain_core.messages import SystemMessage, HumanMessage
from src.config import llm

class Router:
   
       
        
    def route(self, query: str) -> bool:
        """
        Determines if the query is a code-related question or a general question.
        
        Returns:
            bool: True if code question, False if general question
        """
        
        system_prompt = """You are a routing agent that determines if a user's query is about code or a general question.

Analyze the user's query and respond with ONLY ONE WORD:

- "CODE" - if asking about specific functions, classes, methods, or code implementation
- "CHAT" - if asking general questions, concepts, or casual conversation

- "Explain the add_var function"
- "How does the build method work?"
- "What does the _scope function return?"
- "Show me the VectorStoreBuilder class"
- "What calls the _add_var function?"

- "What is a vector database?"
- "How do I install Python?"
- "What are best practices for error handling?"
- "Hello, how are you?"
- "Explain what semantic indexing means"

**RESPOND WITH ONLY ONE WORD: "CODE" OR "CHAT"**
"""

        user_message = f"Query: {query}"
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ])
            
            if isinstance(response, str):
                content = response
            else:
                content = response.content if hasattr(response, 'content') else str(response)
            
            content = content.strip().upper()
            
            print (content)
            
            return content == "CHAT"
            
        except Exception as e:
            print(f"Router error: {e}")
            return False


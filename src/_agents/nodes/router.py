from src.config import llm

class Router:
    def __init__(self):
        self.system_prompt = """You are a Senior Technical Router. 
Classify the user query into ONE of these categories:

1. **CODE**: Asking about specific classes, functions, variables, or code blocks.
   - Examples: "What does process_data() do?", "Show me the login function"

2. **PROJECT**: Asking about the overall project purpose and what it does.
   - Examples: "What does this project do?", "Explain this project", "Project overview"

3. **FLOW**: Asking about execution flow, architecture, or how things connect.
   - Examples: "Show me the flow", "How does it work?", "Explain the architecture", "Flow diagram"

4. **CHAT**: General conversation, greetings, or non-technical queries.
   - Examples: "Hi", "Thanks", "Hello"

Output ONLY: "CODE", "PROJECT", "FLOW", or "CHAT".
"""

    def route(self, user_query):
        """Routes the query to appropriate handler"""
        
        query_lower = user_query.lower()
    
        if any(word in query_lower for word in ['hi', 'hello', 'hey', 'thanks', 'thank you']):
            return 'CHAT'
        if any(phrase in query_lower for phrase in ['flow', 'diagram', 'architecture', 'call graph']):
            return 'FLOW'
        if any(phrase in query_lower for phrase in ['what does this project', 'explain this project', 'project overview', 'what is this project']):
            return 'PROJECT'
        response = llm.invoke([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query}    ])
        
        category = response.content.strip().upper()
    
        if category not in ['CODE', 'PROJECT', 'FLOW', 'CHAT']:
            return 'CODE'
        return category
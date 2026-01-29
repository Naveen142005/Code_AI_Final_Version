from langchain_core.messages import SystemMessage, HumanMessage
from src.config import llm
from src._agents.state import AgentState

class GeneralAssistant:
    def __init__(self):
        pass
    def respond(self, query: str) -> str:
        print(f"[General Assistant] => Generating response for: '{query}'")
        
        system_prompt = """You are a helpful AI assistant integrated into a Codebase Analysis Tool.
Your primary job is to answer general questions clearly, accurately, and concisely.

## Guidelines:
- If the user greets you (Hi, Hello), respond politely and ask how you can help with their code.
- If the user asks a general programming question, provide a helpful summary.
- Be conversational and friendly.
- If the question is about the SPECIFIC codebase loaded in the context but you ended up here, apologize and suggest they ask specific questions about the code structure.

## Tone:
- Professional yet approachable.
- Concise. No fluff.
"""

        try:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ])
            
            content = response.content if hasattr(response, 'content') else str(response)
            return content
            
        except Exception as e:
            print(f"[General Assistant] => Error: {e}")


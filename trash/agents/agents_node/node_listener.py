
import json
import re
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.agents_node.state import AgentState
from src.config import llm

def node_listener(state: AgentState):
    raw_query = state.get("input", "").strip()
    current_focus = state.get("context_focus")
    
    safe_query = raw_query[:2000]
    
    resolved_query = raw_query

    context_block = f"ACTIVE CONTEXT: {current_focus}" if current_focus else "ACTIVE CONTEXT: NO PRIOR CONTEXT (Treat input as a fresh topic)"

    system_prompt = """You are a query disambiguation engine for a static analysis AI.
    Your specific job is to rewrite the user's query to be self-contained, replacing relative pronouns with specific file names from context.

    RULES:
    1. IF user uses pronouns (it, this, that, the function), replace them with the ACTIVE CONTEXT name.
    2. IF user switches topic or names a specific file, ignore ACTIVE CONTEXT.
    3. IF user inputs code snippets or logs, do not rewrite the code, just return the intent.
    4. IF input is a greeting or clear, return it exactly as is.
    5. OUTPUT ONLY the rewritten query string. No quotes, no preamble."""

    user_prompt = f"""
    {context_block}
    
    USER INPUT:
    "{safe_query}"
    """

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        cleaned_response = response.content.strip().strip('"').strip("'")
        
        if cleaned_response and len(cleaned_response) < len(safe_query) * 2:
            resolved_query = cleaned_response

    except Exception:
        pass

    return {
        "resolved_query": resolved_query,
        "retry_count": 0,
        "critique_reason": "",
        "tool_history": [],
        "research_results": "RESET",
        "diagram_results": "RESET"
    }

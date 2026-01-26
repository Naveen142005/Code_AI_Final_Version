
import json
import re
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AgentState
from config import llm

VALID_TOOLS = {
    "ConceptSearch", 
    "StructureInspector", 
    "FileReader", 
    "DiagramGenerator", 
    "SymbolTracker", 
    "ProjectOutline",
    "GeneralChat" 
}

def clean_json_text(text: str) -> str:
    text = text.replace("```json", "").replace("```", "").strip()
    text = re.sub(r"//.*", "", text)
    return text

def node_router(state: AgentState) -> Dict[str, Any]:
    query = state.get("resolved_query", state.get("input", ""))
    tool_history = state.get("tool_history", [])
    last_critique = state.get("critique_reason", "")

    critique_block = ""
    if last_critique:
        critique_block = f"""
        ⚠️ PREVIOUS PLAN FAILED.
        Reason: "{last_critique}"
        Tried: {tool_history}
        TASK: Pick a DIFFERENT strategy.
        """

    system_prompt = f"""You are the Lead Architect for a Codebase AI. 
    Select the BEST tools to answer the query.

    AVAILABLE TOOLS:
    1. ConceptSearch: "How does X work?", "Explain logic". (Semantic)
    2. SymbolTracker: "Where is X?", "Find usages". (Exact)
    3. StructureInspector: "Who calls X?", "Inheritance". (Graph)
    4. FileReader: "Refactor", "Fix bug", "Read file". (Disk)
    5. DiagramGenerator: "Draw", "Visualize", "Chart".
    6. ProjectOutline: "What is this repo?", "Folder structure".
    7. GeneralChat: ONLY for greetings ("Hi"), compliments ("Good job"), or generic "Help me" requests.

    {critique_block}

    RULES:
    - IF the query is PURELY conversational (e.g., "Hello", "Who are you?"), select ["GeneralChat"].
    - IF the query has ANY technical intent (e.g., "Hi, explain auth"), IGNORE the greeting and select the technical tool (e.g., ["ConceptSearch"]).
    - Select MULTIPLE tools if needed.
    
    OUTPUT FORMAT:
    Return strictly valid JSON:
    {{
        "tools": ["ToolName1"],
        "reasoning": "Brief reason."
    }}
    """

    user_prompt = f"QUERY: {query}"

    selected_tools = []
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        cleaned_json = clean_json_text(response.content)
        parsed = json.loads(cleaned_json)
        
        raw_tools = parsed.get("tools", [])
        if isinstance(raw_tools, str): raw_tools = [raw_tools]
        
        selected_tools = [t for t in raw_tools if t in VALID_TOOLS]
        
        print(f"[Router] => Selected: {selected_tools} ({parsed.get('reasoning')})")

    except Exception:
        if "hi" in query.lower().split() or "hello" in query.lower().split():
             selected_tools = ["GeneralChat"]
        else:
             selected_tools = ["ConceptSearch"]
        print(f"[Router] => Error. Fallback to: {selected_tools}")

    
    if not selected_tools:
        selected_tools = ["GeneralChat"]

    return {
        "plan_step": "routing_complete",
        "selected_tools": selected_tools
    }


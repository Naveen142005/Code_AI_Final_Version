
import json
import re
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AgentState
from config import llm

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

# nodes/node_worker.py

import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from state import AgentState
from config import llm
from tools.registry import get_tools_by_name

def node_worker(state: AgentState):
    """
    👷 Node C: The Executor (Worker)
    Goal: Bind tools, inject context, and execute with precision.
    """
    # 1. UNPACK STATE
    selected_strategies = state.get("selected_tools", [])
    resolved_query = state.get("resolved_query", "")
    context_focus = state.get("context_focus", "None")

    # Safety: Default to ConceptSearch if router failed (Self-Healing)
    if not selected_strategies:
        selected_strategies = ["ConceptSearch"]

    print(f"👷 [Worker] Strategies: {selected_strategies} | Focus: {context_focus}")

    # 2. FETCH EXECUTABLE TOOLS
    active_tools = get_tools_by_name(selected_strategies)
    
    if not active_tools:
        print("   ⚠️ No executable tools found. Skipping.")
        return {"plan_step": "execution_skipped"}

    # 3. BIND TOOLS TO LLM
    # This restricts the LLM to ONLY use what was authorized.
    llm_with_tools = llm.bind_tools(active_tools)

    # 4. CONTEXT-AWARE PROMPT (The "Pro" Feature)
    # We tell the LLM about the 'context_focus' so it can fill missing arguments.
    system_prompt = f"""You are the Senior Executor.
    
    CONTEXT FOCUS: {context_focus}
    (Use this file/symbol name if the user implies "it" or "current file".)
    
    ASSIGNED TOOLS: {[t.name for t in active_tools]}
    
    YOUR JOB:
    1. Analyze the query: "{resolved_query}"
    2. Call the necessary tools with PRECISE arguments.
    3. If you need to read a file but don't know the exact path, call 'list_files_tool' first.
    """

    # 5. INVOKE THE BRAIN
    try:
        # We assume the input is just the prompt since we bound tools
        ai_msg = llm_with_tools.invoke([SystemMessage(content=system_prompt)])
    except Exception as e:
        print(f"   ⚠️ LLM Binding Crash: {e}")
        return {"research_results": [f"Error: {e}"]}

    # 6. EXECUTE TOOLS
    research_outputs = []
    diagram_outputs = []
    
    if ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            call_id = tool_call["id"]
            
            print(f"   🔨 Invoking: {tool_name}({tool_args})")
            
            # Find the matching tool object
            selected_tool = next((t for t in active_tools if t.name == tool_name), None)
            
            if selected_tool:
                try:
                    # --- EXECUTION ---
                    result = selected_tool.invoke(tool_args)
                    
                    # --- FORMATTING ---
                    # Header helps the Judge understand what happened
                    output_block = (
                        f"### TOOL OUTPUT: {tool_name}\n"
                        f"Args: {tool_args}\n"
                        f"Content:\n{result}\n"
                    )
                    
                    # --- ROUTING ---
                    if "diagram" in tool_name.lower():
                        diagram_outputs.append(output_block)
                    else:
                        research_outputs.append(output_block)
                        
                except Exception as e:
                    error_block = f"### TOOL ERROR: {tool_name}\nError: {str(e)}\n"
                    research_outputs.append(error_block)
    else:
        # Fallback: LLM refused to call tools (maybe it knows the answer?)
        if ai_msg.content:
             research_outputs.append(f"### LLM THOUGHTS:\n{ai_msg.content}")

    # 7. UPDATE STATE
    # Note: We return lists because the State reducer (operator.add) appends them.
    return {
        "research_results": research_outputs,
        "diagram_results": diagram_outputs,
        "tool_history": selected_strategies # Log strategies, not raw tool names
    }
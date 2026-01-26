import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from src.agents.agents_node.state import AgentState
from src.config import llm
from src.tools.tools import get_tools_by_name

def node_worker(state: AgentState):
   
    selected_strategies = state.get("selected_tools", [])
    resolved_query = state.get("resolved_query", "")
    context_focus = state.get("context_focus", "None")

    if not selected_strategies:
        selected_strategies = ["ConceptSearch"]

    print(f"[node worker] => strategies: {selected_strategies} | Focus: {context_focus}")

    active_tools = get_tools_by_name(selected_strategies)
    
    if not active_tools:
        print(" No tools found.sad life Skipping...")
        return {"plan_step": "execution_skipped"}

   
    llm_with_tools = llm.bind_tools(active_tools)

  
    context_instruction = ""
    
    if context_focus and context_focus != "None":
        context_instruction = f"""
        PRIORITY INSTRUCTION:
        The file '{context_focus}' is CONFIRMED to exist. 
        - Do NOT verify it. 
        - Do NOT call list_files_tool to check for it.
        - Call read_file_tool('{context_focus}') IMMEDIATELY.
        """

    system_prompt = f"""You are the Senior Executor.
    
    CONTEXT FOCUS: {context_focus}
    ASSIGNED TOOLS: {[t.name for t in active_tools]}
    
    {context_instruction}
    
    YOUR JOB:
    1. Analyze the query: "{resolved_query}"
    2. Execute the necessary tools.
    
    RULES:
    - If the user implies "it" or "read this", USE THE CONTEXT FOCUS.
    - Only list files if the path is completely unknown.
    """

    try:
        ai_msg = llm_with_tools.invoke([SystemMessage(content=system_prompt)])
    except Exception as e:
        print(f"   ⚠️ LLM Binding Crash: {e}")
        return {"research_results": [f"Error: {e}"]}

    research_outputs = []
    diagram_outputs = []
    
    if ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            call_id = tool_call["id"]
            
            print(f"   🔨 Invoking: {tool_name}({tool_args})")
            
            selected_tool = next((t for t in active_tools if t.name == tool_name), None)
            
            if selected_tool:
                try:
                    result = selected_tool.invoke(tool_args)
                    
                    output_block = (
                        f"### TOOL OUTPUT: {tool_name}\n"
                        f"Args: {tool_args}\n"
                        f"Content:\n{result}\n"
                    )
                    print ('Output - block')
                    print(output_block)
                    
                    if "diagram" in tool_name.lower():
                        diagram_outputs.append(output_block)
                    else: 
                        research_outputs.append(output_block)
                        
                except Exception as e:
                    error_block = f"### TOOL ERROR: {tool_name}\nError: {str(e)}\n"
                    research_outputs.append(error_block)
    else:
        if ai_msg.content:
             research_outputs.append(f"### LLM THOUGHTS:\n{ai_msg.content}")

   
    return {
        "research_results": research_outputs,
        "diagram_results": diagram_outputs,
        "tool_history": selected_strategies 
    }
 
  
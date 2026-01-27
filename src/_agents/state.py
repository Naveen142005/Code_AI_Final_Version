import operator
from typing import Annotated, List, TypedDict, Union

class AgentState(TypedDict):

    input: str
    query: str
    
    chat: bool
    
    research_results: str
    
    resolved_query: str
    prompt_final: str
    
    is_ok: bool
    
    final_response: str
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
# def manage_memory(existing: List, new: Union[List, str]): 
#     if new == "RESET": return [] 
#     return existing + new
    
    # chat_history: Annotated[List[str], manage_memory] 
    # retry_count: int
    # tool_history: List[str]
    # critique_reason: str
    # diagram_results: str
    # context_focus: str 

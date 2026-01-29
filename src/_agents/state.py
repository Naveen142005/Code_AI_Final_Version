
import operator
from typing import Annotated, Any, List, Optional, TypedDict, Union,Dict

class AgentState(TypedDict):

    input: str
    query: str
    
    chat: bool
    
    is_first: bool = False
    
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

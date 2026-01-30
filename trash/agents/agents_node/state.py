import operator
from typing import Annotated, List, TypedDict, Union

def manage_memory(existing: List, new: Union[List, str]): 
    if new == "RESET": return [] 
    return existing + new

class AgentState(TypedDict):
    chat_history: Annotated[List[str], manage_memory] 
    context_focus: str 

    input: str
    selected_tools: List[str]
    
    resolved_query: str
    is_expendable: bool

    research_results: Annotated[List[str], manage_memory] 
    diagram_results: Annotated[List[str], manage_memory]
    
    retry_count: int
    critique_reason: str
    tool_history: List[str]
    
    final_response: str

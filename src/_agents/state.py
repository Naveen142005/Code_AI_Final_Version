
import operator
from typing import  TypedDict

class AgentState(TypedDict):

    input: str #Repo_Url
    query: str #User Query
    
    router_response: str   #Router response  
    
    is_repo_loaded: bool = False #is it first time repo loading ? or already repo loaded ?
    
    research_results: str # Explanation chunks releated to the query
    
    
    overview_prompt: str #Over view question's Prompt
    resolved_query: str #Storing most releated chunk to the query for expending
    explanation_prompt: str #Code explanation prompt
     
    is_expendable: bool 
    
    final_response: str #Final result
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
# def manage_memory(existing: List, new: Union[List, str]): 
#     if new == "RESET": return [] 
#     return existing + new
    
    # chat_history: Annotated[List[str], manage_memory] 
    # retry_count: int
    # tool_history: List[str]
    # critique_reason: str
    # diagram_results: str
    # context_focus: str 

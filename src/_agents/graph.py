from langgraph.graph import StateGraph, END, START
from src._agents.all_nodes import *
from src._agents.state import AgentState

def should_continue_after_grader(state: AgentState) -> str:
    is_ok = state.get('is_ok', False)
    
    if is_ok:
        return "expand" 
    else:
        return "presenter"


def route_after_router(state: AgentState) -> str:
    chat = state.get('chat', False)

    print('_' * 90)
    print (chat)
    if chat:
        return "general_assistant"  
    else:
        return "retriever"  


def start_after(state: AgentState) -> str:
    """Only check if we have input (repo already loaded)"""
    has_input = not (state.get('is_first'))
    
    print("=" * 40)
    print(f"[START] Input exists: {has_input}")
    print(f"[START] Route: {'router' if has_input else 'repo_loader'}")
    print("=" * 40)
    
    return 'router' if has_input else 'repo'


def create_graph():
    

    workflow = StateGraph(AgentState)
    
   
    workflow.add_node("repo_loader", repo_loader)
    workflow.add_node("build_vector", build_vector)
    workflow.add_node("build_bm25", build_bm25)
    workflow.add_node("build_graph", build_graph)
    workflow.add_node("router", router_node)
    workflow.add_node("retriever", retriver_node)
    workflow.add_node("grader", grader_node)
    workflow.add_node("expander", expander_node)
    workflow.add_node("presenter", presenter_node)
    workflow.add_node('general_assistant', general_assistant_node)
    
   
    workflow.add_conditional_edges(
        START,
        start_after,
        {
            "repo": "repo_loader",
            "router": "router"
        }
    )
    
   
    workflow.add_edge("repo_loader", "build_vector")
    workflow.add_edge("build_vector", "build_bm25")
    workflow.add_edge("build_bm25", "build_graph")
    workflow.add_edge("build_graph", "router")
    
   
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "retriever": "retriever",
            "general_assistant": "general_assistant"
        }
    )
    
   
    workflow.add_edge("retriever", "grader")
    workflow.add_conditional_edges(
        "grader",
        should_continue_after_grader,
        {
            "expand": "expander",
            "presenter": "presenter"
        }
    )
    
    workflow.add_edge("expander", "presenter")
    workflow.add_edge("presenter", END)
    workflow.add_edge("general_assistant", END)
   
    graph = workflow.compile(
        interrupt_before=["router"],
        checkpointer=None 
    )
    
    return graph

app = create_graph()

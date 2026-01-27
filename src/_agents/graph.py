from langgraph.graph import StateGraph, END
from src._agents.all_nodes import *
from src._agents.state import AgentState

def should_continue_after_grader(state: AgentState) -> str:
    is_ok = state.get('is_ok', False)
    
    if is_ok:
        return "expand"
    else:
        return "presenter"


def route_after_router(state: AgentState) -> str:
    is_code = state.get('chat', False)
    
    if is_code:
        return "retriever"
    else:
        return "presenter"


def route_after_repo_loader(state: AgentState) -> str:
    """Check if repo URL exists to decide build or skip"""
    if state.get('input', ''):
        return 'build'
    return 'router'


def create_graph():
    """Create and compile the LangGraph workflow"""
    
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
    
    
    workflow.set_entry_point("repo_loader")
    
    
    workflow.add_conditional_edges(
        "repo_loader",
        route_after_repo_loader,
        {
            "build": "build_vector",  
            "router": "router"         
        }
    )
    
    
    workflow.add_edge("build_vector", "build_bm25")
    workflow.add_edge("build_bm25", "build_graph")
    workflow.add_edge("build_graph", "router")
    
    
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "retriever": "retriever",
            "presenter": "presenter"
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
    
    
    graph = workflow.compile(interrupt_before=["router"])
    
    return graph

app = create_graph()

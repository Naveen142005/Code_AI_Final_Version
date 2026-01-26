from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import os, sys

import sys
print ("="*40)
print(sys.path)


from .state import AgentState
from agents.agents_node.node_final import node_final
from agents.agents_node.node_judger import node_judge
from agents.agents_node.node_listener import node_listener
from agents.agents_node.node_router import node_router
from agents.agents_node.node_worker import node_worker


def route_from_brain(state: AgentState):
   
    tools = state.get("selected_tools", [])
    
    if "GeneralChat" in tools or not tools:
        print("[Graph] => Route: Chat Mode -> final")
        return "node_final"
    
    print("[Graph] => Route: Work Mode -> Worker")
    return "node_worker"

def route_from_judge(state: AgentState):
 
    is_ok = state.get("is_ok", False)
    
    if is_ok:
        print("[Graph] => Route: Quality PASS -> final")
        return "node_final"
    else:
        print("[Graph] => Route: Quality FAIL -> Router (Retry)")
        return "node_router"



def build_graph():
   
    workflow = StateGraph(AgentState)

    workflow.add_node("node_listener", node_listener)
    workflow.add_node("node_router", node_router)
    workflow.add_node("node_worker", node_worker)
    workflow.add_node("node_judge", node_judge)
    workflow.add_node("node_final", node_final)

    
    workflow.set_entry_point("node_listener")
    
    workflow.add_edge("node_listener", "node_router")
    
    workflow.add_conditional_edges(
        "node_router",
        route_from_brain,
        {
            "node_worker": "node_worker",
            "node_final": "node_final"
        }
    )
    
    workflow.add_edge("node_worker", "node_judge")
    
    workflow.add_conditional_edges(
        "node_judge",
        route_from_judge,
        {
            "node_final": "node_final",
            "node_router": "node_router"
        }
    )
    
    workflow.add_edge("node_final", END)


    checkpointer = MemorySaver()
    
    app = workflow.compile(checkpointer=checkpointer)
    return app


graph = build_graph()
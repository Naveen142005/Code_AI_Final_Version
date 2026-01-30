from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import os, sys
import sys


print ("="*40)
print(sys.path)


from src.agents.agents_node.node_final import node_final
from src.agents.agents_node.node_judger import node_judge
from src.agents.agents_node.node_listener import node_listener
from src.agents.agents_node.node_router import node_router
from src.agents.agents_node.node_worker import node_worker

from src.agents.agents_node.state import AgentState

def route_from_brain(state: AgentState):
   
    tools = state.get("selected_tools", [])
    print ("=" * 60)
    
    print (tools)
    if "GeneralChat" in tools or not tools:
        print("[Graph] => Route: Chat Mode -> final")
        return "node_final"
    
    print("[Graph] => Route: Work Mode -> Worker")
    return "node_worker"

def route_from_judge(state: AgentState):
 
    is_expendable = state.get("is_expendable", False)
    
    if is_expendable:
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


    # checkpointer = MemorySaver()
    
    app = workflow.compile()
    # app = workflow.compile(checkpointer=checkpointer)
    return app


graph = build_graph()
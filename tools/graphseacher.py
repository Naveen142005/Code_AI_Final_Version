import pickle
from config import *


class GraphSearchTool:
    def __init__(self):
        self.graph = None
        
        print('[Graph Search tool] => Is Loading...]')
        
        if os.path.exists(GRAPH_OUTPUT_FILE):
            with open(GRAPH_OUTPUT_FILE, "rb") as f:
                self.graph = pickle.load(f)
            print(f"[Graph Search tool] =>  Nodes: {len(self.graph.nodes)}, Edges: {len(self.graph.edges)}")
        else:
            print("[Graph Search tool] => Graph File Not Found! Run Phase 2.")
    
    def get_node(self, node_id):
        """Return detail about speafic node.."""
        
        if not self.graph:
            print('[Graph Search tool] => Graph not Found')
        if node_id not in self.graph:
            print (f"[Graph Search tool] => Node '{node_id}' not found in the graph.")
            return f"Node '{node_id}' not found in the graph."
        
        #Getting node's Meta data
        node_data = self.graph.nodes[node_id]
        
        #Successor -> Children of this node
        #Predecessors -> Parent of this node
        
        children = list(self.graph.successors(node_id))
        parents = list(self.graph.predecessors(node_id))
        
        return {
            "id": node_id,
            "type": node_data.get("type", "unknown"),
            "role": node_data.get("role", "code"),
            "definition_line": node_data.get("start"),
            "file": node_data.get("file"),
            "calls": children[:10],       
            "called_by": parents[:10]  
        }
        
    def get_inheritance(self, node_id: str):
        """
        find parent classes (if this is a class).
        """
        
        if not self.graph or node_id not in self.graph: return []
        
        bases = []
        for neighbor in self.graph.successors(node_id):
            edge_data = self.graph.get_edge_data(node_id, neighbor)
            if edge_data and edge_data.get("relation") == "inherits":
                bases.append(neighbor)
        
        return bases
        
        
import networkx as nx
import os
import pickle
import config 

class DiagramGenerator:
    def __init__(self):
        self.graph = None
        print('[Diagram Tool] => Loading Graph...')
        
        if os.path.exists(config.GRAPH_OUTPUT_FILE):
            with open(config.GRAPH_OUTPUT_FILE, "rb") as f:
                self.graph = pickle.load(f)
            print(f"[Diagram Tool] => Graph Loaded. Nodes: {len(self.graph.nodes)}, Edges: {len(self.graph.edges)}")
        else:
            print("[Diagram Tool] => Graph File Not Found!")

    def generate(self, node_ids: list[str], depth: int = 2):
        if not self.graph: return "Error: Graph not loaded."
        if not node_ids: return "Error: No nodes provided."

        # BFS Traversal
        relevant_nodes = set(node_ids)
        curr = set(node_ids)
        
        for _ in range(depth):
            next = set()
            for n_id in curr:
                if n_id in self.graph:
                    # check neighbors (Parents & Children)
                    neighbors = list(self.graph.successors(n_id)) + list(self.graph.predecessors(n_id))
                    
                    for neighbor in neighbors:
                        
                        node_data = self.graph.nodes[neighbor]
                        node_type = node_data.get("type", "unknown")
                        
                        if node_type == "external": 
                            continue
                            
                        next.add(neighbor)
            
            relevant_nodes.update(next)
            curr = next

    
        if len(relevant_nodes) > 50:
             return f"Error: Diagram too complex ({len(relevant_nodes)} nodes). Filtered out external libs but still too big. Try depth=1."

        #build clusters and edges
        clusters = {} 
        edges = []
        
        for n_id in relevant_nodes:
            node_data = self.graph.nodes[n_id]
            file_name = node_data.get("file", "unknown")
            
            if file_name == "unknown": continue

            if file_name not in clusters: clusters[file_name] = []
            clusters[file_name].append(n_id)
            
            # Build Edges
            for child in self.graph.successors(n_id):
                if child in relevant_nodes:
                    src = self._clean_id(n_id)
                    tar = self._clean_id(child)
                    edges.append(f"    {src} --> {tar}")

        # generate Mermaid Syntax
        mermaid_lines = ["graph TD"]
        
        mermaid_lines.append("    classDef fileNode fill:#f9f,stroke:#333,stroke-width:2px;")
        mermaid_lines.append("    classDef funcNode fill:#bbf,stroke:#333,stroke-width:1px;")

        for file_name, nodes in clusters.items():
            cluster_id = self._clean_id(file_name)
            clean_filename = os.path.basename(file_name)
            
            mermaid_lines.append(f"    subgraph {cluster_id} [{clean_filename}]")
            
            for n_id in nodes:
                safe_id = self._clean_id(n_id)
                node_data = self.graph.nodes[n_id]
                node_type = node_data.get("type", "code")
                
                if node_type == "file":
                    label = os.path.basename(n_id.replace("file::", ""))
                    mermaid_lines.append(f"        {safe_id}[\"{label}\"]:::fileNode")
                else:
                    label = n_id.split(".")[-1]
                    mermaid_lines.append(f"        {safe_id}[\"{label}\"]:::funcNode")

            mermaid_lines.append("    end")

        mermaid_lines.extend(set(edges))
        
        return "\n".join(mermaid_lines)

    def _clean_id(self, text):
        return text.replace(".", "_").replace(":", "_").replace("/", "_").replace("-", "_")

# --- TEST AREA ---
if __name__ == "__main__":
    generator = DiagramGenerator()
    if generator.graph:
        # Auto-find a function node to test
        test_node = None
        for n, data in generator.graph.nodes(data=True):
            if data.get("type") == "function" and "ingestion" in str(data.get("file", "")):
                test_node = n
                break
        
        if test_node:
            print(f"--- Generating Diagram for: {test_node} ---")
            print(generator.generate([test_node], depth=2))
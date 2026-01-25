import json
import os
import pickle
import networkx as nx

# --- CONFIGURATION ---
INPUT_FILE = "semantic_graph_v2.json"
OUTPUT_DIR = "./storage"
GRAPH_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "structure_graph.pkl")
DEPENDENCY_MAP_FILE = os.path.join(OUTPUT_DIR, "dependency_map.json")

class GraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

    def build(self):
        print("🏗️  [Graph] Loading Phase 1 Data...")
        if not os.path.exists(INPUT_FILE):
            raise FileNotFoundError(f"Missing {INPUT_FILE}. Run Phase 1 first.")

        with open(INPUT_FILE, "r") as f:
            data = json.load(f)

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        print(f"🕸️  [Graph] Processing {len(nodes)} nodes and {len(edges)} edges...")
        # print (nodes, edges)

        # 1. Add Nodes with Metadata
        for node in nodes:
            # We store all metadata (complexity, role, lines) in the graph node
            # This allows the "Router" in Phase 3 to make decisions quickly.
            print(node)
            self.graph.add_node('./temp_repo' + node["id"], **node)

        # 2. Add Edges with Context
        outgoing_map = {} # Helper for Vector Store (Dependency Injection)

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            
            # Add to NetworkX
            self.graph.add_edge(
                source, 
                target, 
                relation=edge["relation"],
                is_protected=edge.get("is_protected", False),
                context=edge.get("context", [])
            )

            # Build Dependency Map (Who calls whom?)
            # We only care about Function-to-Function calls for summaries
            if edge["relation"] == "calls":
                if source not in outgoing_map: outgoing_map[source] = []
                outgoing_map[source].append(target)

        # 3. Save the Graph (Pickle is fastest for NetworkX)
        print("->" , self.graph)
        print("="*70)
        print(outgoing_map)
        print(f"💾 [Graph] Saving Graph to {GRAPH_OUTPUT_FILE}...")
        with open(GRAPH_OUTPUT_FILE, "wb") as f:
            pickle.dump(self.graph, f)

        # 4. Save Dependency Map (Improvement)
        # We save this as JSON so the Vector Store can read it easily 
        # without loading the heavy NetworkX object.
        print(f"💾 [Graph] Saving Dependency Map to {DEPENDENCY_MAP_FILE}...")
        with open(DEPENDENCY_MAP_FILE, "w") as f:
            json.dump(outgoing_map, f, indent=2)

        print("✅ [Graph] Build Complete.")

if __name__ == "__main__":
    builder = GraphBuilder()
    builder.build()
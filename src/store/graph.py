import builtins
import pickle
import networkx as nx
import json
import os
import inspect
from src.config import *

class GraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            
        self.BUILTIN_NAMES = self.collect_builtin_names()
        
    def collect_builtin_names(self):
        """Collects built-in functions AND methods (e.g. split, append, get)"""
        names = set(dir(builtins))
        for obj in vars(builtins).values():
            if inspect.isclass(obj):
                
                names.update(dir(obj))
        return names

    def is_builtin_name(self, name):
        return name in self.BUILTIN_NAMES

    def correct_id(self, bad_id):
        """Standardize IDs to dots."""
        if not bad_id: return ""
        return bad_id.replace("/", ".").replace("\\", ".").replace(".py", "").replace("::", ".")
    
    def build(self):
        print('[Graph] => Loading the ingestion data')
        
        if not os.path.exists(INPUT_FILE):
            raise FileNotFoundError(f'Missing ingestion data')
        
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
        
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        
        print(f'[Graph] => Processing {len(nodes)} nodes with {len(edges)} edges')
        
        
        for node in nodes:
            clean_id = self.correct_id(node['id'])
            self.graph.add_node(
                clean_id,
                file_id=node['id'], 
                **node 
            )
        
        outgoing_edge_map = {} 
        
        
        for edge in edges:
            src = edge['source']
            tar = edge['target']
            
            if tar.startswith('external::'):
                try:
                    tar = tar.split('::')[-1]
                except:
                    pass            
            src = self.correct_id(src)
            tar = self.correct_id(tar)
            
            is_internal_function = self.graph.has_node(tar)
            
            if not is_internal_function:
                short_name = tar.split('.')[-1]
                if self.is_builtin_name(short_name): 
                    continue
            
            if tar == src: continue
            
            if "safe" in src or "safe" in tar:
                print(f"  [Link] {src} --> {tar}")
            
            self.graph.add_edge(
                src,
                tar,
                relation=edge['relation'],
                context=edge.get('context', []) 
            )
            
            if edge['relation'] == 'calls':
                if src not in outgoing_edge_map:
                    outgoing_edge_map[src] = []
                if tar not in outgoing_edge_map[src]:
                    outgoing_edge_map[src].append(tar)
            
        print(f'[Graph] => Saving Graph to {GRAPH_OUTPUT_FILE}')
        with open(GRAPH_OUTPUT_FILE, 'wb') as f:
            pickle.dump(self.graph, f)
        
        print(f"[Graph] => Saving Dependency Map to {DEPENDENCY_MAP_FILE}")
        with open(DEPENDENCY_MAP_FILE, 'w') as f:
            json.dump(outgoing_edge_map, f, indent=2)
            
        
        self.print_stats()
        print('[Graph] => Everything Completed !!')

    def print_stats(self):
        """Helper to print graph details nicely"""
        print("\n" + "="*40)
        print(f"📊 GRAPH STATS")
        print("="*40)
        print(f"Nodes: {self.graph.number_of_nodes()}")
        print(f"Edges: {self.graph.number_of_edges()}")
        print("-" * 40)
        
        print("\n🔍 SAMPLE NODES (First 5):")
        for i, node in enumerate(list(self.graph.nodes())[:5]):
            print(f"  {i+1}. {node}")

        print("\n🔗 SAMPLE EDGES (First 5):")
        for i, (u, v) in enumerate(list(self.graph.edges())[:5]):
            print(f"  {i+1}. {u} --> {v}")
        print("="*40 + "\n")


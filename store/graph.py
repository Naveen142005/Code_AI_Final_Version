import pickle
import networkx as nx
import json
import os
from config import *

class GraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
    
    def build(self):
        """ Building the dependency Graph"""
        
        print('[Graph] => Loading the ingestion data')
        
        
        if not os.path.exists(INPUT_FILE):
            raise FileNotFoundError(f'Missing the ingestion data')
        
        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
        
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        
        if not nodes:
            print('No nodes found')
        if not edges:
            print('No edges found')
        
        print(f'[Graph] => Processing the  {len(nodes)} nodes with {len(edges)} egdes')
        
        # Adding the nodes with metadata
        for node in nodes:
            self.graph.add_node(
                node['id'],  #Id to find a node uniquely
                **node #Node's metadatas
            )
        
        #Adding the edges with context
        outgoing_edge_map = {} #Helps in vector store
        
        for edge in edges:
            src = edge['source']
            tar = edge['target']
            
            self.graph.add_edge(
                src,
                tar,
                relation = edge['relation'],
                is_protected = edge.get('is_protected', False), # refering the try_block
                context = edge.get('context', []) # like function, if, else
            )
        
        
            if edge['relation'] == 'calls':
                if src not in outgoing_edge_map:
                    outgoing_edge_map[src] = []
                outgoing_edge_map[src].append(tar)
            
        print(f'[Graph Builder] => Graph saving to the {GRAPH_OUTPUT_FILE}')
        
        with open(GRAPH_OUTPUT_FILE, 'wb') as f:
            pickle.dump(self.graph, f)
        
        
        print(f"[Graph Builder] => Saving Dependency Map to {DEPENDENCY_MAP_FILE}")

        with open(DEPENDENCY_MAP_FILE, 'w') as f:
            json.dump(outgoing_edge_map, f, indent=2)
        
        print('[Graph Builder] => Everything Completed !!')
        

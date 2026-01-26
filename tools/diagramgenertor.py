import os
import pickle
import re
import networkx as nx
from langchain_core.tools import tool
from config import *

class DiagramGenerator:
    def __init__(self):
        self.graph = None
        print('[Diagram Tool] => Loading Graph...')
        
        if os.path.exists(GRAPH_OUTPUT_FILE):
            with open(GRAPH_OUTPUT_FILE, "rb") as f:
                self.graph = pickle.load(f)
            print(f"[Diagram Tool] => Graph Loaded. Nodes: {len(self.graph.nodes)}")
        else:
            print("[Diagram Tool] => Graph File Not Found!")
            
        self.bm25 = None
        self.bm25_nodes = None
        
        
        if os.path.exists(BM25_PATH):
            with open(BM25_PATH, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["model"]
                self.bm25_nodes = data["node_map"]
                print("[Exact matcher Tool] => Ready to match.")
        else:pass

    def _clean_id(self, text):
        """Helper to remove illegal characters for Mermaid syntax"""
        return text.replace(".", "_").replace(":", "_").replace("/", "_").replace("-", "_").replace("__", "")

    def _smart_resolve(self, user_query: str) -> str:
        """
        The 'God Mode' Resolver.
        Converts 'bm25 indexing' -> 'store/bm25_index.BM25Builder'.
        """
        if not self.graph: return None
        
        if user_query in self.graph.nodes:
            return user_query

        print(f"[DiagramEngine] 🔍 Resolving '{user_query}'...")

        if self.bm25:
            q_tokens = user_query.lower().split()
            scores = self.bm25.get_scores(q_tokens)
            
            best_idx = max(range(len(scores)), key=lambda i: scores[i])
            if scores[best_idx] > 0:
                best_node = self.bm25_nodes[best_idx]
                print(f"   -> BM25 Match: '{best_node}'")
                return best_node

        candidates = []
        q_tokens = set(re.split(r'\W+', user_query.lower()))
        
        for node_id in self.graph.nodes:
            node_tokens = set(re.split(r'\W+', node_id.lower()))
            
            overlap = len(q_tokens.intersection(node_tokens))
            
            if overlap > 0:
                score = overlap * 100 - len(node_id)
                candidates.append((score, node_id))
        
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_match = candidates[0][1]
            print(f"   -> Token Match: '{best_match}'")
            return best_match

        return None

    def generate(self, node_ids: list[str], depth: int = 2):
        """
        Generates Mermaid.js syntax.
        """
        
        if not self.graph:
            return "Error: Knowledge Graph not loaded. Run Phase 2."
        
        if not node_ids:
            return "Error: No nodes provided for diagram."

        resolved_roots = []
        for query in node_ids:
            real_id = self._smart_resolve(query)
            if real_id:
                resolved_roots.append(real_id)
            else:
                pass 
        
        if not resolved_roots:
             return f"Error: Could not resolve any code entities from '{node_ids}'. Try using exact filenames."

        relevant_nodes = set(resolved_roots)
        curr = set(resolved_roots)
        
        for _ in range(depth):
            next = set()
            for n_id in curr:
                if n_id in self.graph:
                    neighbors = list(self.graph.successors(n_id)) +  list(self.graph.predecessors(n_id))
                    
                    for neighbor in neighbors:
                        node_data = self.graph.nodes[neighbor]
                        if node_data.get("type") == "external": continue
                        next.add(neighbor)
            
            relevant_nodes.update(next)
            curr = next

        if len(relevant_nodes) > 60:
            return f"Error: Diagram too complex ({len(relevant_nodes)} nodes). Try reducing depth."

        arr = {} 
        edges = []
        
        for n_id in relevant_nodes:
            node_data = self.graph.nodes[n_id]
            file_name = node_data.get("file", "unknown")
            
            if file_name == "unknown": continue

            if file_name not in arr: arr[file_name] = []
            arr[file_name].append(n_id)
            
            for child in self.graph.successors(n_id):
                if child in relevant_nodes:
                    src = self._clean_id(n_id)
                    tar = self._clean_id(child)
                    edges.append(f"    {src} --> {tar}")

        mermaid_lines = ["graph TD"]
        mermaid_lines.append("    classDef fileNode fill:#f9f,stroke:#333,stroke-width:2px;")
        mermaid_lines.append("    classDef funcNode fill:#bbf,stroke:#333,stroke-width:1px;")

        for file_name, nodes in arr.items():
            cluster_id = self._clean_id(file_name)
            clean_filename = os.path.basename(file_name)
            
            mermaid_lines.append(f"    subgraph {cluster_id} [{clean_filename}]")
            
            for n_id in nodes:
                safe_id = self._clean_id(n_id)
                node_data = self.graph.nodes[n_id]
                node_type = node_data.get("type", "code")

                label = n_id.split(".")[-1]
                
                if node_type == "file":
                    mermaid_lines.append(f"        {safe_id}[\"{label}\"]:::fileNode")
                else:
                    mermaid_lines.append(f"        {safe_id}[\"{label}\"]:::funcNode")

            mermaid_lines.append("    end")

        mermaid_lines.extend(set(edges))
        
        return "\n".join(mermaid_lines)

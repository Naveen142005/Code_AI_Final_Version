import os
import pickle
from langchain_core.tools import tool
from config import *


class ExactMatchTool:
    def __init__(self):
        self.bm25 = None
        self.bm25_nodes = None
        
        print("[Exact matcher Tool] => loading BM25 index..")
        
        if os.path.exists(BM25_PATH):
            with open(BM25_PATH, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["model"]
                self.bm25_nodes = data["node_map"]
                print("[Exact matcher Tool] => Ready to match.")
        else:
            print(f"[Exact matcher Tool] => BM25 index not found in {BM25_PATH}")

    def lookup(self, symbol_name: str):
       
        if not self.bm25:
            return "Error: BM25 index not loaded. Cannot perform exact lookup."
        
        print(f"[Exact matcher Tool] => Finding: '{symbol_name}'")


        query = symbol_name.lower().split()
        scores = self.bm25.get_scores(query)
        
       
        top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:10]
        
        hits = []
        for i in top_n:
            if scores[i] > 0:
                node_id = self.bm25_nodes[i]
                hits.append(node_id)
                
        if not hits:
            return f"No exact matches found for '{symbol_name}'."
            
        return f"Found '{symbol_name}' in these locations:\n" + "\n".join(hits)

import os
import json

from src.ingestion.analyzer import analyze_codebase
from src.ingestion.repo_loader import RepoLoader
from src.store.bm25 import BM25Builder
from src.store.graph import GraphBuilder
from src.store.vector import VectorStoreBuilder
 

REPO_PATH = "./temp_repo"
OUTPUT_FILE = "semantic_graph_v2.json"


class Main:
    
    def main(self, repo_url):
   
        if not repo_url:
            print("No URL provided.")
            exit()


        loader = RepoLoader(repo_url)
        
        if not os.path.exists(REPO_PATH):
            print(f"Error: Path '{REPO_PATH}' does not exist.")
        else:
            data = analyze_codebase(REPO_PATH)
            
            with open(OUTPUT_FILE, "w") as f:
                json.dump(data, f, indent=2)

            print(f"   Graph saved to {OUTPUT_FILE}")
            print(f"   Files: {data['stats']['files']}")
            print(f"   Definitions: {data['stats']['definitions']}")
            print(f"   Calls/Edges: {data['stats']['calls']}")
            
        # builder = GraphBuilder()
        # builder.build()
        
        # indexer = BM25Builder()
        # indexer.build()

        # builder = VectorStoreBuilder()
        # builder.build()
        
        
        

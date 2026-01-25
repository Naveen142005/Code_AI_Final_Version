import os
import json

from analyzer import analyze_codebase
from repo_loader import RepoLoader


REPO_PATH = "./temp_repo"
OUTPUT_FILE = "semantic_graph_v2.json"


if __name__ == "__main__":
   
    repo_url = input('[Repo Loader] => Enter GitHub URL: ').strip()
    if not repo_url:
        print("No URL provided.")
        exit()


    loader = RepoLoader(repo_url)
    loader.load(REPO_PATH)
    
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
        

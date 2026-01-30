import os
from src._agents.nodes.expand import expander
from src.config import REPO_PATH
import networkx as nx

def find_entry_point(repo_path):
    
    repo_path = os.path.abspath(repo_path)

    common_names = ["main.py", "app.py", "run.py", "manage.py", "start.py", "cli.py"]
    for name in common_names:
        full_path = os.path.join(repo_path, name)
        if os.path.exists(full_path):
            return os.path.relpath(full_path, repo_path) 
    
    for root, _, files in os.walk(repo_path):
        
        if any(x in root for x in ["venv", "env", "tests", "node_modules", ".git"]): 
            continue

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        if 'if __name__' in f.read():
                            return os.path.relpath(full_path, repo_path) 
                except:
                    continue

    return None

if __name__ == "__main__":
    start_file = find_entry_point(REPO_PATH)
    
    if start_file:
       print()
    G =  expander().get_graph()
    
    all_connected = G.descendants(G, "file::"+start_file)

    print(f"Start Point: Main")
    print(f"All Connected Nodes: {all_connected}")
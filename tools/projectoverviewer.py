import os
import pickle
from langchain_core.tools import tool
from tools.filereader import FileReader
from config import *

class ProjectOverViewTool:
    def __init__(self):
        self.graph = None
        
        print('[Project Overviewer tool] => Is Loading...]')
        
        if os.path.exists(GRAPH_OUTPUT_FILE):
            with open(GRAPH_OUTPUT_FILE, "rb") as f:
                self.graph = pickle.load(f)
            print(f"[Project Overviewer tool] =>  Nodes: {len(self.graph.nodes)}, Edges: {len(self.graph.edges)}")
        else:
            print("[Project Overviewer tool] => Graph File Not Found! Run Phase 2.")
            
     

    def get_readme(self):
        """Scans the repo for the best README file."""
        readme_candidates = []
        
       
        for root, dirs, files in os.walk(REPO_PATH):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if "readme" in file.lower():
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, REPO_PATH)
                    
                    depth = rel_path.count(os.sep) #root readme -> best, other no best
                    readme_candidates.append((depth, rel_path, full_path))

        #sort -> shortest depth first,then shortest filename
        readme_candidates.sort(key=lambda x: (x[0], len(x[1])))
        
        if not readme_candidates:
            return "README: Not found in repository.\n"

        best_depth, best_rel_path, best_full_path = readme_candidates[0]
        print(f"[Project Overviewer tool] => Found README file at: {best_rel_path}")
        
        try:
            with open(best_full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(2000) # Read first 2000 chars
                if len(content) >= 2000:
                    content += "\n... [Truncated] ..."
                return f"README ({best_rel_path}):\n{content}\n"
        except Exception as e:
            return f"README found at {best_rel_path} but could not be read: {e}\n"

    def get_core_files(self):
        """Returns the top files based on Graph Gravity(PageRank)."""
        
        important_nodes = []
        
        if self.graph:
            # sort by gravity(descending)
            sorted_nodes = sorted(
                self.graph.nodes(data=True), 
                key=lambda x: x[1].get('gravity', 0), 
                reverse=True
            )
            
            count = 0
            for n_id, meta in sorted_nodes:
                #skip external libs, only show project files
                if meta.get("type") != "external" and "file::" in n_id:
                    clean_id = n_id.replace("file::", "")
                    score = meta.get('gravity', 0)
                    important_nodes.append(f"  - {clean_id} (Importance: {score:.4f})")
                    count += 1
                if count >= 8: break 
        
        if not important_nodes:
            return "CORE FILES: Graph not available or no high-gravity files found.\n"
            
        return f"CORE FILES (Most heavily referenced):\n" + "\n".join(important_nodes) + "\n"

    def generate_outline(self):
        """Combines Readme, Core Files, and File Tree."""
        print(f"[Project Overviewer tool] => [Project Engine] Generating outline...")
        output_parts = []
        
        # README
        output_parts.append(self.get_readme())
        
        # Core Files
        output_parts.append(self.get_core_files())
        
        tree = FileReader.list_files()
        output_parts.append(f"PROJECT FILE TREE:\n{tree}")
        
        return "\n".join(output_parts)

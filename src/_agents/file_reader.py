import os
import pickle
from src.config import REPO_PATH, GRAPH_OUTPUT_FILE

class FileReader_:
    def __init__(self):
        
        self.root_path = os.path.abspath(REPO_PATH)
        self.graph = None
        
        
        if os.path.exists(GRAPH_OUTPUT_FILE):
            with open(GRAPH_OUTPUT_FILE, "rb") as f:
                self.graph = pickle.load(f)
        else:
            print(f"[FileReader] => Warning: Graph file not found at {GRAPH_OUTPUT_FILE}")

    def _get_safe_path(self, file_path):
        """
        Sanitizes file path to ensure it stays within the repo directory.
        Removes any accidental 'temp_repo' prefixes from legacy data.
        """
        clean = file_path.replace("\\", "/")
        
        
        prefixes = ["./temp_repo/", "temp_repo/", "file::"]
        for p in prefixes:
            if clean.startswith(p):
                clean = clean.replace(p, "", 1)
            
        clean = clean.lstrip("./").lstrip("/")
        
        
        return os.path.join(self.root_path, clean)
    
    def correct_id(self, bad_id):
        """Standardize IDs to dots."""
        if not bad_id: return ""
        return bad_id.replace("/", ".").replace("\\", ".").replace(".py", "").replace("::", ".")
    
    def read_file(self, node_id, with_lines=True):
        """
        Reads a specific slice of a file based on the Node ID.
        """
        
        if not self.graph:
            return "Error: Graph not loaded."

        if node_id not in self.graph.nodes:
            node_id = self.correct_id(node_id)
            if node_id not in self.graph.nodes: 
                return f"Error: Node '{node_id}' not found in graph."

        node_data = self.graph.nodes[node_id] 
        file_path = node_data.get('file', '')
        start_line = node_data.get('start', 1)
        end_line = node_data.get('end', None) 
        
        try:
            full_path = self._get_safe_path(file_path)
            
            
            if not os.path.abspath(full_path).startswith(self.root_path):
                 return f"Error: Access denied. {file_path} is outside the repository."

            if not os.path.exists(full_path):
                return f"Error: File '{file_path}' not found."

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            
            start_idx = max(0, start_line - 1)
            
            
            if end_line:
                end_idx = min(len(lines), end_line)
                selected_lines = lines[start_idx : end_idx]
            else:
                selected_lines = lines[start_idx:]

            if with_lines:
                with_num = []
                for i, line in enumerate(selected_lines):
                    num = start_line + i
                    with_num.append(f"{num:4d} | {line.rstrip()}")
                return "\n".join(with_num)
            else:
                return "".join(selected_lines)

        except Exception as e:
            return f"Error reading file: {str(e)}"
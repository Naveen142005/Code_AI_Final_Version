import os
import pickle
# from src._agents.nodes.expand import expander
import src.config as config
from src.config import *

class FileReader_:
    def __init__(self):
        self.root_path = os.path.abspath(config.REPO_PATH)
        # print(f"[File Reader] =>  Root: {self.root_path}")
        self.graph = None
        if os.path.exists(GRAPH_OUTPUT_FILE):
            with open(GRAPH_OUTPUT_FILE, "rb") as f:
                self.graph = pickle.load(f)

    def _get_safe_path(self, file_path):
        """Helper to safely join paths."""
        clean = file_path.replace("\\", "/")
        if clean.startswith("./temp_repo/"):
            clean = clean.replace("./temp_repo/", "", 1)
        elif clean.startswith("temp_repo/"):
            clean = clean.replace("temp_repo/", "", 1)
            
        clean = clean.lstrip("./").lstrip("/")
        return os.path.join(self.root_path, clean)

    def read_file(self, node_id, with_lines=True):
        """
        Reads a file safe with line numbers.
        """
        
        if node_id not in self.graph.nodes:
            return f"Error: Node '{node_id}' not found in graph."

    
        node_data = self.graph.nodes[node_id] 
        

        file_path = node_data['file']
        start_line = node_data.get('start', 0)
        end_line = node_data.get('end', 0)
        
        # print('+++++++++++++++++++++++++++++++++++++++')
        # print(node_data)
        # print (file_path)
        # print(start_line)
        # print(end_line)
        # print('+++++++++++++++++++++++++++++++++++++++')
        
        try:
            full_path = self._get_safe_path(file_path)
            # print (full_path).
            
            if not full_path.startswith(self.root_path):
                 return f"Error: Access denied. {file_path} is outside the repository."

            if not os.path.exists(full_path):
                return f"Error: File '{file_path}' not found."

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            
            # print('------------------------------------')
            # print (lines)
            # print('------------------------------------')

            start_line = max(1, start_line) 
            end_line = min(len(lines), end_line)
            # print ('st',start_line)
            # print('end', end_line)
            selected_lines = lines[start_line-1 : end_line]

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


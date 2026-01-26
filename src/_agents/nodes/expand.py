import os
import pickle
from src._agents.file_reader import FileReader_
from src.config import *

class expander:
    def __init__(self):
        self.graph = None
        self.reader = FileReader_()
        
        if os.path.exists(GRAPH_OUTPUT_FILE):
            with open(GRAPH_OUTPUT_FILE, "rb") as f:
                self.graph = pickle.load(f)
        else:
            pass

    def get_graph(self):
        return self.graph

    def _clean_node_id(self, node_id):
        return node_id.split('.')[-1]

    def _fetch_context_code(self, node_list):
        """
        Helper: Fetches the FULL code of neighboring nodes.
        No truncation.
        """
        context_map = {}
        for node_id in node_list:
            full_code = self.reader.read_file(node_id)
            if full_code:
                context_map[self._clean_node_id(node_id)] = full_code
        return context_map

    def expand(self, node_id):
        if not self.graph or node_id not in self.graph.nodes:
            return None

        code_body = self.reader.read_file(node_id)
        
        parents = list(self.graph.predecessors(node_id))
        relevant_parents = [p for p in parents if "external" not in self.graph.nodes[p].get("type", "")][:5]

        children = list(self.graph.successors(node_id))
        relevant_children = [c for c in children if "external" not in self.graph.nodes[c].get("type", "")][:5]

        parent_codes = self._fetch_context_code(relevant_parents)
        child_codes = self._fetch_context_code(relevant_children)

        parent_names = [self._clean_node_id(p) for p in relevant_parents]
        child_names = [self._clean_node_id(c) for c in relevant_children]

        node_data = self.graph.nodes[node_id]

        return {
            "id": node_id,
            "file_path": node_data.get('file'),
            "type": node_data.get('type', 'code'),
            "code_body": code_body,
            
            "parent_context": parent_codes,
            "child_context": child_codes,

            "parents_list": parent_names,
            "children_list": child_names,
            "context_str": (
                f"**Triggered By:** {', '.join(parent_names) if parent_names else 'None'}\n"
                f"**Uses:** {', '.join(child_names) if child_names else 'None'}"
            )
        }
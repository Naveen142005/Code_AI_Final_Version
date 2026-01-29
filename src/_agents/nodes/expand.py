import os
import pickle
import ast
from src._agents.file_reader import FileReader_ 
from src.config import *

class expander:
    def __init__(self):
        self.graph = None
        self.reader = FileReader_()
        
        if os.path.exists(GRAPH_OUTPUT_FILE):
            with open(GRAPH_OUTPUT_FILE, "rb") as f:
                self.graph = pickle.load(f)

    def get_graph(self):
        return self.graph

    def _clean_node_id(self, node_id):
        return node_id.split('.')[-1]
    
    def correct_id(self, bad_id):
        if not bad_id: return ""
        return bad_id.replace("/", ".").replace("\\", ".").replace(".py", "").replace("::", ".")

    def _generate_stub(self, code_content):

        try:
            if len(code_content.splitlines()) < 15:
                return code_content

            tree = ast.parse(code_content)
            
            doc = False
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if ast.get_docstring(node):
                        doc = True
                        break
            
            if doc:
                class doc_create(ast.NodeTransformer):
                    def visit_FunctionDef(self, node):
                        doc_node = ast.get_docstring(node)
                        new_body = []
                        if doc_node:
                            new_body.append(ast.Expr(value=ast.Constant(value=doc_node)))
                        new_body.append(ast.parse("pass # ... (Implementation Hidden) ... #").body[0])
                        node.body = new_body
                        return node
                    
                    def visit_ClassDef(self, node):
                        self.generic_visit(node)
                        return node

                new_tree = doc_create().visit(tree)
                return ast.unparse(new_tree)
            else:
                lines = code_content.splitlines()
                return "\n".join(lines[:15]) + "\n\n# ... (Rest of code hidden) ..."

        except Exception:

            lines = code_content.splitlines()
            return "\n".join(lines[:10]) + "\n# ... (Truncated) ..."

    def _fetch_context_code(self, node_list):
        context_map = {}
        for node_id in node_list:
            full_code = self.reader.read_file(node_id)
            if full_code:
                context_map[self._clean_node_id(node_id)] = self._generate_stub(full_code)
        return context_map

    def _format_code_section(self, code_dict, section_title):
        if not code_dict:
            return f"**{section_title}:** None\n"
        
        formatted = f"**{section_title}:**\n"
        for i, (name, code) in enumerate(code_dict.items(), 1):
            formatted += f"\n{i}. [{name}]\n"
            formatted += f"{code}\n"
            formatted += "-" * 50 + "\n"
        
        return formatted

    def expand(self, node_id):
        if not self.graph: return None

        if node_id not in self.graph.nodes:
            node_id = self.correct_id(node_id)

        if node_id not in self.graph.nodes:
            return None
            
        code_body = self.reader.read_file(node_id)
        
        #limit neighbors to 2 to save tokens
        parents = list(self.graph.predecessors(node_id))
        relevant_parents = [p for p in parents if "external" not in self.graph.nodes[p].get("type", "")][:2]

        children = list(self.graph.successors(node_id))
        relevant_children = [c for c in children if "external" not in self.graph.nodes[c].get("type", "")][:2]

        parent_codes = self._fetch_context_code(relevant_parents)
        child_codes = self._fetch_context_code(relevant_children)

        parent_names = [self._clean_node_id(p) for p in relevant_parents]
        child_names = [self._clean_node_id(c) for c in relevant_children]

        node_data = self.graph.nodes[node_id]
        
        formatted_explanation = f"""
{'=' * 60}
FOCUS CODE (Full Content)
{'=' * 60}
{code_body}

{'=' * 60}
{self._format_code_section(parent_codes, "CALLED BY (Context)")}
{'=' * 60}
{self._format_code_section(child_codes, "CALLS TO (Context)")}
{'=' * 60}
"""

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
            ),
            
            "formatted_explanation": formatted_explanation.strip()
        }
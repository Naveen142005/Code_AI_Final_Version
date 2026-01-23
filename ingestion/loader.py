import os
import ast

REPO_PATH = "./temp_repo"
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'env', 'node_modules', 'dist'}

class SymbolIndexer(ast.NodeVisitor):
    def __init__(self, rel_path):
        self.rel_path = rel_path
        self.definitions = {} 
        self.class_stack = []

    def visit_ClassDef(self, node):
        self.definitions.setdefault(node.name, []).append(self.rel_path)
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        name = node.name
        if self.class_stack:
            name = f"{self.class_stack[-1]}.{name}"
        
        # Store LIST of files where this name appears
        self.definitions.setdefault(name, []).append(self.rel_path)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

class GraphVisitor(ast.NodeVisitor):
    def __init__(self, rel_file_path, definition_map):
        self.rel_file_path = rel_file_path
        self.definition_map = definition_map # name -> [files]
        self.current_scope = None 
        self.edges = []
        self.aliases = {} 
        self.variables = {}
        # Tracks explicit imports: "flipkart_page" -> "seleniumScrape.py"
        self.imported_sources = {} 

    def visit_ImportFrom(self, node):
        # from temp_repo.seleniumScrape import flipkart_page
        module_path = node.module # "temp_repo.seleniumScrape"
        # Guess the file path from module path
        guessed_file = module_path.split(".")[-1] + ".py" 
        
        for alias in node.names:
            target = alias.asname if alias.asname else alias.name
            self.aliases[target] = alias.name
            
            # Store where it came from!
            # We map "flipkart_page" -> "seleniumScrape.py"
            # (This is a simple heuristic; a real compiler is more strict)
            self.imported_sources[target] = guessed_file
            
        self.generic_visit(node)

    def _get_call_chain(self, node):
        if isinstance(node, ast.Name): return (node.id, None)
        elif isinstance(node, ast.Call): return self._get_call_chain(node.func)
        elif isinstance(node, ast.Attribute):
            root, _ = self._get_call_chain(node.value)
            return (root, node.attr) if root else (None, None)
        return (None, None)

    def visit_Call(self, node):
        root_name, method_name = self._get_call_chain(node.func)
        
        if root_name:
            resolved_root = self.aliases.get(root_name, root_name)
            final_root = self.variables.get(resolved_root, resolved_root)
            
            call_key = f"{final_root}.{method_name}" if method_name else final_root
            
            # --- COLLISION RESOLUTION LOGIC ---
            target_file = None
            
            # 1. Did we explicitly import it? (e.g. from X import login)
            if root_name in self.imported_sources:
                potential_file = self.imported_sources[root_name]
                # Check if this file is in our definition list for this function
                candidates = self.definition_map.get(call_key, [])
                for candidate in candidates:
                    if potential_file in candidate: # Heuristic match
                        target_file = candidate
                        break

            # 2. Is it defined in the CURRENT file? (Local Priority)
            if not target_file:
                candidates = self.definition_map.get(call_key, [])
                if self.rel_file_path in candidates:
                    target_file = self.rel_file_path
            
            # 3. Fallback: If only 1 exists globally, pick it.
            if not target_file:
                candidates = self.definition_map.get(call_key, [])
                if len(candidates) == 1:
                    target_file = candidates[0]
                elif len(candidates) > 1:
                    # Ambiguous! We don't know which one.
                    # For now, pick the first one, or log a warning.
                    target_file = candidates[0] 

            if target_file:
                caller = f"{self.rel_file_path}::{self.current_scope or '[global]'}"
                target = f"{target_file}::{call_key}"
                
                if caller != target:
                     self.edges.append({
                        "source": caller,
                        "target": target,
                        "relation": "calls",
                        "snippet": f"{root_name}.{method_name or ''}"
                    })

        self.generic_visit(node)
        
    # visit_Assign, visit_FunctionDef, etc... (Same as before)
    # ... (Include other visitor methods) ...

class RobustGraphBuilder: 
    # ... (Standard Boilerplate, update run() to handle list merging) ...
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)
        self.files = []
        self.definition_map = {} 
        self.edges = []

    def run(self):
        # 1. Scan
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if file.endswith(".py"):
                    self.files.append(os.path.join(root, file))

        # 2. Index (Merge lists)
        for file_path in self.files:
            rel = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    tree = ast.parse(f.read())
                indexer = SymbolIndexer(rel)
                indexer.visit(tree)
                
                # MERGE DICTIONARIES CORRECTLY
                for k, v_list in indexer.definitions.items():
                    if k not in self.definition_map:
                        self.definition_map[k] = []
                    self.definition_map[k].extend(v_list)
                    
            except: pass

        # 3. Link
        for file_path in self.files:
            rel = os.path.relpath(file_path, self.root_dir).replace("\\", "/")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    tree = ast.parse(f.read())
                visitor = GraphVisitor(rel, self.definition_map)
                visitor.visit(tree)
                self.edges.extend(visitor.edges)
            except: pass

        return self.edges

if __name__ == "__main__":
    builder = RobustGraphBuilder(REPO_PATH)
    graph = builder.run()
    for e in graph:
        print(f"{e['source']} --> {e['target']}")
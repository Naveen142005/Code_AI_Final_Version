# import ast
# import os
# import json
# import builtins
# import networkx as nx  
# from collections import defaultdict
# from git import Repo

# REPO_PATH = "./temp_repo"  
# IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'env', 'node_modules', 'dist', 'tests', 'docs', 'site-packages'}
# MAX_FUNCTION_LIMIT = 300  


# def safe_name(node):
#     """Safely extracts the name from AST nodes (handling attributes, subscripts, etc)"""
#     if isinstance(node, ast.Name):
#         return node.id
#     if isinstance(node, ast.Attribute):
#         parent = safe_name(node.value)
#         return f"{parent}.{node.attr}" if parent else node.attr
#     if isinstance(node, ast.Call):
#         return safe_name(node.func)
#     if isinstance(node, ast.Subscript):
#         if hasattr(node.slice, 'value'): 
#              return safe_name(node.slice.value)
#         return safe_name(node.slice)
#     return None

# def get_docstring(node):
#     """Extracts docstring from a node if present"""
#     return ast.get_docstring(node) or ""

# def calculate_complexity(node):
#     """Calculates  Complexity  """
#     complexity = 1
#     for child in ast.walk(node):
#         if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler, ast.With)):
#             complexity += 1
#     return complexity


# class SemanticIndexer(ast.NodeVisitor):
#     def __init__(self, file_path, rel_path, global_class_registry):
#         self.file_path = file_path
#         self.rel_path = rel_path
#         self.module_name = rel_path.replace(".py", "").replace(os.sep, ".")
#         self.global_class_registry = global_class_registry 

#         self.scope_stack = [self.module_name]
#         self.definitions = {}
#         self.calls = []
        
        
#         self.context_stack = [] 
        
#         self.scope_aliases = defaultdict(dict)
#         self.scope_vars = defaultdict(dict)
#         self.return_types = {} 
#         self.current_class = None

#     def _scope(self):
#         return ".".join(self.scope_stack)

#     def _add_alias(self, name, real):
#         self.scope_aliases[self._scope()][name] = real

#     def _add_var(self, name, vtype):
#         if not vtype: return
#         self.scope_vars[self._scope()][name] = vtype

#     def _find_alias(self, name):
#         temp = list(self.scope_stack)
#         while temp:
#             scope = ".".join(temp)
#             if name in self.scope_aliases.get(scope, {}):
#                 return self.scope_aliases[scope][name]
#             temp.pop()
#         return name

#     def _find_var_type(self, name):
#         temp = list(self.scope_stack)
#         while temp:
#             scope = ".".join(temp)
#             if name in self.scope_vars.get(scope, {}):
#                 return self.scope_vars[scope][name]
#             temp.pop()
        
#         # Global Registry Check
#         if "." in name:
#             obj, attr = name.split(".", 1)
#             obj_type = self._find_var_type(obj)
#             if obj_type and obj_type in self.global_class_registry:
#                  return self.global_class_registry[obj_type].get(attr)
#         return None

#     def _resolve_import_path(self, module, level):
#         if level == 0: return module
#         parts = self.module_name.split(".")
#         if level > len(parts): return module
#         base = ".".join(parts[:-level])
#         return f"{base}.{module}" if module else base


#     def visit_Import(self, node):
#         for a in node.names:
#             self._add_alias(a.asname or a.name, a.name)

#     def visit_ImportFrom(self, node):
#         module = self._resolve_import_path(node.module or "", node.level)
#         for a in node.names:
#             full_name = f"{module}.{a.name}"
#             self._add_alias(a.asname or a.name, full_name)

#     def visit_ClassDef(self, node):
#         full = f"{self._scope()}.{node.name}"
#         bases = [safe_name(b) for b in node.bases]

#         role = "class"
#         if any("Model" in b for b in bases): role = "db_model"
#         if any("Exception" in b for b in bases): role = "exception"

#         self.definitions[full] = {
#             "type": "class",
#             "file": self.rel_path,
#             "start": node.lineno,
#             "end": node.end_lineno,
#             "bases": bases,
#             "docstring": get_docstring(node),
#             "role": role  
#         }
        
#         prev_class = self.current_class
#         self.current_class = full
#         self.scope_stack.append(node.name)
#         self.generic_visit(node)
#         self.scope_stack.pop()
#         self.current_class = prev_class

#     def visit_FunctionDef(self, node):
#         self._handle_function(node, False)

#     def visit_AsyncFunctionDef(self, node):
#         self._handle_function(node, True)

#     def _handle_function(self, node, is_async):
#         full = f"{self._scope()}.{node.name}"
        
#         ret_type = safe_name(node.returns) if node.returns else "Unknown"
#         if ret_type: ret_type = self._find_alias(ret_type)
#         self.return_types[full] = ret_type

#         decorators = [safe_name(d) for d in node.decorator_list if safe_name(d)]
#         role = "function"
#         if any("route" in d or "get" in d or "post" in d for d in decorators): role = "api_endpoint"
#         if any("task" in d or "celery" in d for d in decorators): role = "background_task"

        
#         start_line = node.lineno
#         end_line = getattr(node, 'end_lineno', start_line) 
        
#         line_count = end_line - start_line
        
#         complexity = calculate_complexity(node)

#         self.definitions[full] = {
#             "type": "function",
#             "file": self.rel_path,
#             "start": start_line,
#             "end": end_line,
#             "async": is_async,
#             "return_type": ret_type,
#             "docstring": get_docstring(node),
#             "complexity": complexity,  
#             "lines": line_count,       
#             "is_huge": line_count > MAX_FUNCTION_LIMIT, 
#             "decorators": decorators,
#             "role": role
#         }

#         self.scope_stack.append(node.name)
#         self.context_stack.append("function") 
        
#         # Handle Args
#         for arg in node.args.args:
#             arg_type = "Unknown"
#             if arg.annotation:
#                 arg_type = self._find_alias(safe_name(arg.annotation))
#             if arg.arg == "self" and self.current_class:
#                 arg_type = self.current_class
#             self._add_var(arg.arg, arg_type)

#         self.generic_visit(node)
#         self.context_stack.pop() 
#         self.scope_stack.pop()

#     def visit_Try(self, node):
#         self.context_stack.append("try_block") 
#         self.generic_visit(node)
#         self.context_stack.pop()

#     def visit_If(self, node):
#         self.context_stack.append("condition") 
#         self.generic_visit(node)
#         self.context_stack.pop()

#     def visit_For(self, node):
#         self.context_stack.append("loop")      
#         self.generic_visit(node)
#         self.context_stack.pop()
        
#     def visit_While(self, node):
#         self.context_stack.append("loop")
#         self.generic_visit(node)
#         self.context_stack.pop()

#     def visit_Assign(self, node):
#         vtype = None
#         if isinstance(node.value, ast.Call):
#             func_name = self._find_alias(safe_name(node.value.func))
#             vtype = self.return_types.get(func_name, func_name)
#         elif isinstance(node.value, ast.Name):
#             vtype = self._find_var_type(node.value.id)

#         if vtype:
#             for t in node.targets:
#                 if isinstance(t, ast.Name):
#                     self._add_var(t.id, vtype)
#                 elif isinstance(t, ast.Attribute) and safe_name(t.value) == "self" and self.current_class:
#                     if self.current_class not in self.global_class_registry:
#                         self.global_class_registry[self.current_class] = {}
#                     self.global_class_registry[self.current_class][t.attr] = vtype
#         self.generic_visit(node)

#     def visit_Call(self, node):
#         raw_name = safe_name(node.func)
#         scope = self._scope()
#         resolved_target = raw_name

#         if raw_name:
#             alias_target = self._find_alias(raw_name)
#             if alias_target != raw_name:
#                 resolved_target = alias_target
#             elif "." in raw_name:
#                 obj, meth = raw_name.rsplit(".", 1)
#                 vtype = self._find_var_type(obj)
#                 if vtype:
#                     resolved_target = f"{vtype}.{meth}"

#         self.calls.append({
#             "source": scope,
#             "target_hint": resolved_target,
#             "line": node.lineno,
#             "context": list(self.context_stack),
#             "is_protected": "try_block" in self.context_stack 
#         })
#         self.generic_visit(node)



# def analyze_codebase(root_path):
#     print(f"Starting Deep Semantic Analysis: {root_path}")

#     nodes = {}
#     edges = []
    
#     global_class_registry = {}
#     all_defs = {} 
#     all_calls = [] 

#     for root, dirs, files in os.walk(root_path):
#         dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

#         for f in files:
#             if f.endswith(".py"):
#                 full_path = os.path.join(root, f)
#                 rel_path = os.path.relpath(full_path, root_path).replace("\\", "/")
                
#                 file_id = f"file::{rel_path}"
#                 nodes[file_id] = {
#                     "type": "file",
#                     "file": rel_path,
#                     "id": file_id,
#                     "label": os.path.basename(rel_path)
#                 }

#                 try:
#                     with open(full_path, encoding="utf8", errors="ignore") as file_obj:
#                         content = file_obj.read()
#                         tree = ast.parse(content)
                        
#                         idx = SemanticIndexer(full_path, rel_path, global_class_registry)
#                         idx.visit(tree)

#                         all_defs.update(idx.definitions)
#                         all_calls.extend(idx.calls)
                        
#                         for def_id, meta in idx.definitions.items():
#                             edges.append({
#                                 "source": file_id,
#                                 "target": def_id,
#                                 "relation": "contains",
#                                 "confidence": "high"
#                             })

#                 except Exception as e:
#                     print(f" Error parsing {rel_path}: {e}")

#     for def_id, meta in all_defs.items():
#         nodes[def_id] = {
#             "id": def_id,
#             "label": def_id.split(".")[-1],
#             **meta 
#         }

#     print(" Linking Graph Nodes...")

#     name_lookup = defaultdict(list)
#     for k in all_defs:
#         short_name = k.split(".")[-1]
#         name_lookup[short_name].append(k)

#     for c in all_calls:
#         target = c["target_hint"]
#         matches = []
#         confidence = "low"

#         if target in all_defs:
#             matches.append(target)
#             confidence = "high"

#         if not matches:
#              candidates = [k for k in all_defs if k.endswith(f".{target}") or k.endswith(f".{target.split('.')[-1]}")]
#              if candidates:
#                  matches = candidates[:1] 
#                  confidence = "medium"

#         if not matches and "." not in target:
#              matches = name_lookup.get(target, [])
#              confidence = "low"

#         if not matches:
#             if target in dir(builtins): continue
            
#             external_id = f"external::{target}"
#             if external_id not in nodes:
#                 nodes[external_id] = {
#                     "id": external_id,
#                     "type": "external",
#                     "label": target
#                 }
#             matches = [external_id]
#             confidence = "high"

#         for m in matches:
#             edges.append({
#                 "source": c["source"],
#                 "target": m,
#                 "relation": "calls",
#                 "line": c["line"],
#                 "confidence": confidence,
#                 "context": c["context"],         
#                 "is_protected": c["is_protected"] 
#             })

#     print("⚖️ Calculating Code Gravity...")
    
#     G = nx.DiGraph()
#     for n_id in nodes: G.add_node(n_id)
#     for e in edges: G.add_edge(e["source"], e["target"])

#     try:
#         pagerank = nx.pagerank(G, alpha=0.85)
#         for n_id, score in pagerank.items():
#             if n_id in nodes:
#                 nodes[n_id]["gravity"] = score 
#     except Exception as e:
#         print(f"PageRank failed (graph might be empty): {e}")

#     return {
#         "nodes": list(nodes.values()),
#         "edges": edges,
#         "stats": {
#             "files": sum(1 for n in nodes.values() if n.get("type") == "file"),
#             "definitions": len(all_defs),
#             "calls": len(edges)
#         }
#     }

# from git import Repo
# import stat, os, shutil

# class RepoLoader:
#     def __init__(self, repo_url: str) -> None:
#         self.repo_url = repo_url
        
#     def load(self, path_url: str = './temp_repo') -> None:
#         """Cloing the Git repo in local"""
        
#         def remove_readonly(func, path, exc_info):
#             os.chmod(path, stat.S_IWRITE)
#             func(path)
        
#         if os.path.exists(path_url):
#             shutil.rmtree(path_url, onexc = remove_readonly)
    
#         print('Cloning the repo...\n')
        
#         Repo.clone_from(self.repo_url, path_url, depth= 1)
#         print('repo loaded successFully...')

# if __name__ == "__main__":
#     r = input('Enter github url:')
#     repo = RepoLoader(r)
#     repo.load()
    
#     if not os.path.exists(REPO_PATH):
#         print(f" Error: Path '{REPO_PATH}' does not exist.")
#     else:
#         data = analyze_codebase(REPO_PATH)
        
#         out_file = "semantic_graph_v2.json"
#         with open(out_file, "w") as f:
#             json.dump(data, f, indent=2)

#         print(f"✅ Graph saved to {out_file}")
#         print(f"   Files: {data['stats']['files']}")
#         print(f"   Definitions: {data['stats']['definitions']}")
#         print(f"   Calls/Edges: {data['stats']['calls']}")
#         print("\nReady for Phase 2: Vector Injection.")
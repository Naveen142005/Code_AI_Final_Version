# analyzer.py
import os
import ast
import builtins
import networkx as nx
from collections import defaultdict
from src.ingestion.indexer import SemanticIndexer

import src.config as config

def analyze_codebase(root_path):
    print(f" [Analyzer] => Starting Semantic Analysis: {root_path}")

    nodes = {}
    edges = []
    
    global_class_registry = {}
    all_defs = {} 
    all_calls = [] 

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in config.IGNORE_DIRS]

        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, root_path).replace("\\", "/")
                file_id = f"file::{rel_path}"

                try:
                    
                    with open(full_path, encoding="utf8", errors="ignore") as file_obj:
                        content = file_obj.read()
                        lines = content.splitlines()
                        
                    #Intilize the file nodes
                    nodes[file_id] = {
                        "id": file_id,
                        "type": "module",        
                        "file": rel_path,
                        "name": os.path.basename(rel_path),
                        "start": 1,
                        "end": len(lines),       
                       
                    }

                    
                    tree = ast.parse(content)
                    
                    #traverse in the tree get the function, class
                    idx = SemanticIndexer(full_path, rel_path, global_class_registry)
                    idx.visit(tree)
 
                    all_defs.update(idx.definitions)
                    all_calls.extend(idx.calls)
                    

                    #connecting the edges files to the function
                    for def_id, meta in idx.definitions.items():
                        edges.append({
                            "source": file_id,
                            "target": def_id,
                            "relation": "calls"
                        })

                except SyntaxError:
                    print(f" [Analyzer] => Syntax Error in {rel_path}")
                except Exception as e:  
                    print(f" [Analyzer] => Error parsing {rel_path}: {e}")
                    
    #creating all module level nodes        
    for def_id, meta in all_defs.items():
        nodes[def_id] = {
            "id": def_id,
            "label": def_id.split(".")[-1],
            **meta 
        }

    print(" [Analyzer] =>  Linking Graph Nodes...")

    #Graph Linking. 
    name_lookup = defaultdict(list)
    for k in all_defs: #traverser into the all the functions (src.util.solve)
        short_name = k.split(".")[-1]
        name_lookup[short_name].append(k) # [solve] = [src.util.solve]

    for c in all_calls: #mapping function name -> calling name
        target = c["target_hint"] #Calling function name src.util.solve 
        matches = []
            
        if target in all_defs: #checking the function called i same file
            matches.append(target) 
        
        if not matches:
            candidates = [k for k in all_defs if k.endswith(f".{target}")]
            if candidates:
                matches = candidates[:1]
        
        if not matches and "." not in target:
            matches = name_lookup.get(target, [])
        
        if not matches:
            if target in dir(builtins): continue
            
            external_id = f"external::{target}"
            if external_id not in nodes:
                nodes[external_id] = {
                    "id": external_id,
                    "type": "external",
                    "label": target
                }
            matches = [external_id]


        for m in matches:
            edges.append({
                "source": c["source"], #who is calling
                "target": m, #who was called
                "relation": "calls",
                "line": c["line"]
            })


    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "stats": {
            "files": sum(1 for n in nodes.values() if n.get("type") == "module"),
            "definitions": len(all_defs),
            "calls": len(edges)
        }
    }
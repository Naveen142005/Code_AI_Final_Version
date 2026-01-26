# analyzer.py
import os
import ast
import builtins
import networkx as nx
from collections import defaultdict
from src.ingestion.indexer import SemanticIndexer

import src.config as config

def analyze_codebase(root_path):
    print(f" [Analyzer] => Starting Deep Semantic Analysis: {root_path}")

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
                nodes[file_id] = {
                    "type": "file",
                    "file": rel_path,
                    "id": file_id,
                    "label": os.path.basename(rel_path)
                }

                try:
                    with open(full_path, encoding="utf8", errors="ignore") as file_obj:
                        content = file_obj.read()
                        tree = ast.parse(content)
                        
                        idx = SemanticIndexer(full_path, rel_path, global_class_registry)
                        idx.visit(tree)

                        all_defs.update(idx.definitions)
                        all_calls.extend(idx.calls)
                        
                        for def_id, meta in idx.definitions.items():
                            edges.append({
                                "source": file_id,
                                "target": def_id,
                                "relation": "contains",
                                "confidence": "high"
                            })
                except SyntaxError:
                    pass
                except Exception as e:  
                    print(f" [Analyzer] => Error parsing {rel_path}: {e}")

    for def_id, meta in all_defs.items():
        nodes[def_id] = {
            "id": def_id,
            "label": def_id.split(".")[-1],
            **meta 
        }

    print(" [Analyzer] =>  Linking Graph Nodes...")

    name_lookup = defaultdict(list)
    for k in all_defs:
        short_name = k.split(".")[-1]
        name_lookup[short_name].append(k)

    for c in all_calls:
        target = c["target_hint"]
        matches = []
        confidence = "low"

        if target in all_defs:
            matches.append(target)
            confidence = "high"
        
        if not matches:
             candidates = [k for k in all_defs if k.endswith(f".{target}") or k.endswith(f".{target.split('.')[-1]}")]
             if candidates:
                 matches = candidates[:1] 
                 confidence = "medium"
        
        if not matches and "." not in target:
             matches = name_lookup.get(target, [])
             confidence = "low"
        
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
            confidence = "high"

        for m in matches:
            edges.append({
                "source": c["source"],
                "target": m,
                "relation": "calls",
                "line": c["line"],
                "confidence": confidence,
                "context": c["context"],         
                "is_protected": c["is_protected"] 
            })

    
    print(" [Analyzer] => Calculating Code Scores...")
    
    G = nx.DiGraph()
    for n_id in nodes: G.add_node(n_id)
    for e in edges: G.add_edge(e["source"], e["target"])

    try:
        pagerank = nx.pagerank(G, alpha=0.85)
        for n_id, score in pagerank.items():
            if n_id in nodes:
                nodes[n_id]["gravity"] = score 
    except Exception as e:
        print(f" [Analyzer] => PageRank failed: {e}")

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "stats": {
            "files": sum(1 for n in nodes.values() if n.get("type") == "file"),
            "definitions": len(all_defs),
            "calls": len(edges)
        }
    }
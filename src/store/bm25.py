import json
import pickle
import os
import ast
from rank_bm25 import BM25Okapi
from src.config import *

class BM25Builder:
    def __init__(self):
        
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        self.bm25_index = []
            
    def tokenizer(self, text: str):
        clean_text = text.replace("_", " ").replace(".", " ").replace("::", " ")
        clean_text = clean_text.replace("(", " ").replace(")", " ").replace("=", " ")
        clean_text = clean_text.replace("[", " ").replace("]", " ").replace("{", " ").replace("}", " ")
        clean_text = clean_text.replace("/", " ").replace("\\", " ")
    
        tokenized = clean_text.lower().split()
        return tokenized
    
    def read_the_code(self, path: str, start_line, end_line):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    start = max(0, start_line - 1) 
                    end = end_line
                    return "".join(lines[start:end])
            except Exception as e:
                print(f"[BM25] => Error reading {path}: {e}")
                return ""
        return ""

    def get_skeleton_code(self, code_content):
        """Strips function/class bodies to index only global scope (variables, imports)."""
        try:
            lines = code_content.splitlines()
            tree = ast.parse(code_content)
            exclude_indices = set()
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    
                    start_exclude = node.body[0].lineno - 1 
                    end_exclude = node.end_lineno
                    for i in range(start_exclude, end_exclude):
                        exclude_indices.add(i)

            skeleton_lines = []
            for i, line in enumerate(lines):
                if i not in exclude_indices:
                    skeleton_lines.append(line)
                elif i - 1 not in exclude_indices: 
                    
                    skeleton_lines.append("  ... (logic inside function) ...")
            
            return "\n".join(skeleton_lines)
        except:
            return code_content 

    def build(self):
        print(f"[BM25] => Starting Index Build...")

        if not os.path.exists(INPUT_FILE):
            print(f"[BM25] => Input graph file missing at {INPUT_FILE}")
            return

        with open(INPUT_FILE, 'r') as f:
            data = json.load(f)
        
        corpus = []
        node_ids = []
        
        for node in data['nodes']:
            
            if node["type"] not in ["function", "class", "module"]:
                continue            
            
            full_path = os.path.join(REPO_PATH, node['file'])
            
            code_content = self.read_the_code(
                full_path,
                node['start'],
                node['end']
            )
            
            
            if node["type"] == "module":
                final_content = self.get_skeleton_code(code_content)
                
                docx_text = f"FILE: {node['file']} MODULE GLOBAL "
            else:
                final_content = code_content
                docx_text = f"{node['type']} "

            docx_text += f"{node['id']} {node.get('label', '')} "
            
            if node.get("docstring"):
                docx_text += f"{node['docstring']} "
            
            if node.get("args"): 
                docx_text += f"{node['args']} "

            docx_text += f" {final_content}"
                    
            tokens = self.tokenizer(docx_text)
            
            if tokens:
                corpus.append(tokens)
                node_ids.append(node["id"])
                
        if not corpus:
            print('[BM25] => No indexable content found')
            return
            
        
        bm25_model = BM25Okapi(corpus)
        
        package = {
            "model": bm25_model,
            "node_map": node_ids
        }
        
        print(f"[BM25] => Indexed {len(node_ids)} nodes (Functions, Classes, Globals).")
        print(f"[BM25] => Saving index to {BM25_OUTPUT_FILE}...")
        
        with open(BM25_OUTPUT_FILE, "wb") as f:
            pickle.dump(package, f)
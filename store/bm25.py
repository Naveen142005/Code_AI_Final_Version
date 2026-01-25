import json
import pickle,os
from rank_bm25 import BM25Okapi
from config import *

class BM25Builder:
    def __init__(self):
        if not os.path.exists(OUTPUT_DIR):
            os.mkdir(OUTPUT_DIR)
            self.bm25_index = []
            
    def tokenizer (self, code:str):
        """Tokenize the code e.g (max_limit_file -> max , limit, file)"""
        
        clean_text = code.replace("_", " ").replace(".", " ").replace("::", " ")
        clean_text = clean_text.replace("(", " ").replace(")", " ").replace("=", " ")
    
        tokenized = code.replace('_', " ").split(' ')
        return tokenized
    
    def read_the_code(self, path: str, start_line, end_line):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    start = max(0, start_line)
                    end = end_line
                    return "".join(lines[start:end])
            except Exception as e:
                return ""
        
    
    def build(self):
        if not os.path.exists(INPUT_FILE):
            raise FileNotFoundError(f'Missing file {INPUT_FILE}')

        with open (INPUT_FILE, 'r') as f:
            data = json.load(f)
        
        corpus = []
        node_ids = []
        
        for node in data['nodes']:
            if node["type"] not in ["function", "class"]:
                continue            
            docx_text = f'{node['id']}  {node.get('label', ' ')} '
            
            if node.get("docstring"):
                docx_text += f" {node['docstring']} "
            
            if node.get("args"): 
                docx_text += f" {node['args']} "

            code_content = self.read_the_code(
                './temp_repo/' + node['file'],
                node['start'],
                node['end']
            )            
            
            docx_text += f' {code_content}'
            tokens = self.tokenizer(docx_text)
            # print(code_content)
            
            if tokens:
                corpus.append(tokens)
                node_ids.append(node["id"])
                
        # print(corpus)
        if not corpus:
            print ('[BM25] => No indexable content found')
            
        bm25_model = BM25Okapi(corpus)
        
        package = {
            "model": bm25_model,
            "node_map": node_ids
        }
        
        print(f"[BM25] => Saving index to {BM25_OUTPUT_FILE}...")
        
        with open(BM25_OUTPUT_FILE, "wb") as f:
            pickle.dump(package, f)

            
  
            
            
            
        
        

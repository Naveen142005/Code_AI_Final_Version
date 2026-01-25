import json
import os
import pickle
from rank_bm25 import BM25Okapi

# --- CONFIGURATION ---
INPUT_FILE = "semantic_graph_v2.json"
OUTPUT_DIR = "./storage"
BM25_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "bm25_index.pkl")

class BM25Builder:
    def __init__(self):
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

    def _read_code_from_disk(self, file_path, start_line, end_line):
        """Reads the exact lines from the source file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                # Python AST is 1-indexed, List is 0-indexed
                start = max(0, start_line - 1)
                end = end_line
                return "".join(lines[start:end])
        except Exception as e:
            # If file read fails, we just return empty string so indexing doesn't crash
            return ""

    def _tokenize(self, text):
        """
        Custom tokenizer for Code.
        Splits 'process_payment_v2' -> ['process', 'payment', 'v2']
        """
        if not text: return []
        clean_text = text.replace("_", " ").replace(".", " ").replace("::", " ")
        clean_text = clean_text.replace("(", " ").replace(")", " ").replace("=", " ")
        return clean_text.lower().split()

    def build(self):
        print("🔎 [BM25] Building Keyword Index (with Full Code)...")
        
        with open(INPUT_FILE, "r") as f:
            data = json.load(f)

        corpus = []
        node_ids = []

        for node in data["nodes"]:
            # We only index logical units
            if node["type"] not in ["function", "class"]:
                continue

            # --- 1. METADATA ---
            doc_text = f"{node['id']} {node.get('label', '')}"
            
            if node.get("docstring"):
                doc_text += f" {node['docstring']}"
            
            if node.get("args"): 
                doc_text += f" {node['args']}"

            # --- 2. SOURCE CODE (THE FIX) ---
            # We must read the code to find internal variables like 'tax_rate'
        
            code_content = self._read_code_from_disk(
                './temp_repo/' + node["file"], 
                node["start"], 
                node["end"]
            )
            print (code_content)
            print("="*50 + node['type'])
            doc_text += f" {code_content}"

            # Tokenize
            tokens = self._tokenize(doc_text)
            
            if tokens:
                corpus.append(tokens)
                node_ids.append(node["id"])

        if not corpus:
            print("⚠️ [BM25] No indexable content found.")
            return

        # Build Model
        print(f"⚙️  [BM25] Training on {len(corpus)} documents...")
        bm25_model = BM25Okapi(corpus)

        # Save Model & Mapping
        package = {
            "model": bm25_model,
            "node_map": node_ids
        }

        print(f"💾 [BM25] Saving index to {BM25_OUTPUT_FILE}...")
        with open(BM25_OUTPUT_FILE, "wb") as f:
            pickle.dump(package, f)

        print("✅ [BM25] Build Complete.")

if __name__ == "__main__":
    indexer = BM25Builder()
    indexer.build()
import os

REPO_PATH = './temp_repo'

STORAGE_DIR = "./storage"

VECTOR_DB_DIR = os.path.join(STORAGE_DIR, "chroma_db")

BM25_PATH = os.path.join(STORAGE_DIR, "bm25_index.pkl")

MODEL_NAME = "jinaai/jina-embeddings-v2-base-code"
INPUT_FILE = "semantic_graph_v2.json"

OUTPUT_DIR = "./storage"
BM25_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "bm25_index.pkl")


DEPENDENCY_MAP_FILE = os.path.join(OUTPUT_DIR, "dependency_map.json")

GRAPH_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "structure_graph.pkl")

IGNORE_DIRS = {
    '.git', '__pycache__', 'venv', 'env', 'node_modules', 
    'dist', 'tests', 'docs', 'site-packages', '.idea', '.vscode'
}
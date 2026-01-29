import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR) 
DATA_DIR = os.path.join(PROJECT_ROOT, "data_cache")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

REPO_PATH = os.path.join(DATA_DIR, "temp_repo")


STORAGE_DIR = os.path.join(DATA_DIR, "storage")
OUTPUT_DIR = STORAGE_DIR 

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

VECTOR_DB_DIR = os.path.join(STORAGE_DIR, "chroma_db")


BM25_PATH = os.path.join(STORAGE_DIR, "bm25_index.pkl")
BM25_OUTPUT_FILE = BM25_PATH 


INPUT_FILE = os.path.join(DATA_DIR, "semantic_graph_v2.json")
DEPENDENCY_MAP_FILE = os.path.join(STORAGE_DIR, "dependency_map.json")
GRAPH_OUTPUT_FILE = os.path.join(STORAGE_DIR, "structure_graph.pkl")





IGNORE_DIRS = {
    '.git', '__pycache__', 'venv', 'env', 'node_modules', 
    'dist', 'tests', 'docs', 'site-packages', '.idea', '.vscode',
    'data_cache' 
}

MODEL_NAME = "jinaai/jina-embeddings-v2-base-code"

LLM_MODEL = 'llama-3.3-70b-versatile'


api_key = os.getenv('GROQ_API_KEY')

llm = ChatGroq(
    api_key=api_key,
    model=LLM_MODEL,
    temperature=0
)

def get_repo_path():
    """
    Returns the absolute path where the repo is/will be cloned.
    Ensures the directory structure exists.
    """
    if not os.path.exists(REPO_PATH):
        os.makedirs(REPO_PATH, exist_ok=True)
    return REPO_PATH
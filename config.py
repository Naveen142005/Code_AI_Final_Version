import os

from langchain_groq import ChatGroq

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

from dotenv import load_dotenv
load_dotenv()

# LLM_MODEL = 'llama-3.3-70b-versatile'
LLM_MODEL = 'llama-3.1-8b-instant'
api_key = os.getenv('GROQ_API_KEY')


llm = ChatGroq(
    api_key=api_key,
    model= LLM_MODEL,
    temperature=0
)



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REPO_ROOT = os.path.join(BASE_DIR, "temp_repo")

def get_repo_path():
    if not os.path.exists(REPO_ROOT):
        raise FileNotFoundError(f"❌ Could not find the repo at: {REPO_ROOT}")
    return REPO_ROOT
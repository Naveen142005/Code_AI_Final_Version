import json
import os
import shutil
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_core.documents import Document
 
# --- CONFIGURATION ---
INPUT_FILE = "semantic_graph_v2.json"
OUTPUT_DIR = "./storage"
DEPENDENCY_MAP_FILE = os.path.join(OUTPUT_DIR, "dependency_map.json")
VECTOR_DB_DIR = os.path.join(OUTPUT_DIR, "chroma_db")

# Model Settings
# We use a local HuggingFace model wrapper. 
# If you have a Jina API Key, use JinaEmbeddings class instead.
MODEL_NAME = "jinaai/jina-embeddings-v2-base-code"
MAX_CHUNK_SIZE = 2000 # Characters (Jina context is large, but retrieval is better with focused chunks)

class VectorStoreBuilder:
    def __init__(self):
        print(f"🔌 [Vector] Loading Embedding Model: {MODEL_NAME}...")
        # trust_remote_code=True is required for Jina v2
        self.embeddings = HuggingFaceEmbeddings(
            model_name=MODEL_NAME,
            model_kwargs={"device": "cpu", "trust_remote_code": True}
        )
        
        # Python-Aware Splitter
        # This respects indentation and function boundaries
        self.splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=MAX_CHUNK_SIZE,
            chunk_overlap=200
        )
        
        # Load Dependencies (Improvement from Graph Phase)
        self.dependency_map = {}
        if os.path.exists(DEPENDENCY_MAP_FILE):
            with open(DEPENDENCY_MAP_FILE, "r") as f:
                self.dependency_map = json.load(f)

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
            print(f"⚠️ Could not read {file_path}: {e}")
            return ""

    def _generate_context_header(self, node):
        """Creates a header so the AI knows 'Where am I?' even inside a chunk."""
        header = f"FILE: {node['file']}\n"
        header += f"ID: {node['id']}\n"
        header += f"TYPE: {node['type']}\n"
        
        # Inject Social Context (Improvement)
        # If this function calls others, mention it in the header!
        if node['id'] in self.dependency_map:
            deps = self.dependency_map[node['id']][:5] # Limit to 5
            clean_deps = [d.split(".")[-1] for d in deps] # Just function names
            header += f"USES: {', '.join(clean_deps)}\n"
            
        return header

    def build(self):
        print("🧠 [Vector] Starting Ingestion...")
        
        # Clear old DB to prevent duplicates
        if os.path.exists(VECTOR_DB_DIR):
            shutil.rmtree(VECTOR_DB_DIR)

        with open(INPUT_FILE, "r") as f:
            data = json.load(f)

        documents = []
        
        for node in data["nodes"]:
            # Only embed code, not file nodes or external libraries
            if node["type"] not in ["function", "class"]:
                continue

            # 1. Fetch Raw Code
            code_content = self._read_code_from_disk(
                './temp_repo/' + node["file"], 
                node["start"], 
                node["end"]
            )
            
            if not code_content.strip(): continue

            # 2. Prepare Metadata (The Parent Pointer)
            base_metadata = {
                "id": node["id"],
                "file": node["file"],
                "start_line": node["start"],
                "end_line": node["end"],
                "role": node.get("role", "code"),
                "complexity": node.get("complexity", 0)
            }
            
            header = self._generate_context_header(node)

            # 3. Strategy: Chunk vs Whole
            # Even with Jina 8k, chunking helps 'Focus'. 
            # If a function is 3000 chars, passing it whole is fine.
            # If it's 10,000 chars, split it.
            
            if len(code_content) > MAX_CHUNK_SIZE * 1.5:
                # --- Large Function Strategy ---
                chunks = self.splitter.split_text(code_content)
                
                for i, chunk in enumerate(chunks):
                    # We Embed: Header + Chunk
                    # We Retrieve: Metadata -> Disk Read (if needed)
                    doc = Document(
                        page_content=f"{header}\n--- PART {i+1} ---\n{chunk}",
                        metadata={
                            **base_metadata,
                            "is_chunk": True,
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    )
                    documents.append(doc)
            else:
                # --- Small Function Strategy ---
                doc = Document(
                    page_content=f"{header}\n--- FULL BODY ---\n{code_content}",
                    metadata={
                        **base_metadata,
                        "is_chunk": False,
                        "chunk_index": 0,
                        "total_chunks": 1
                    }
                )
                documents.append(doc)

        # 4. Batch Upsert to Chroma
        if documents:
            print(f"🚀 [Vector] Embedding {len(documents)} documents (this may take a while)...")
            
            # Using Chroma as the persistent store
            vector_db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=VECTOR_DB_DIR,
                collection_name="codebase_v1"
            )
            
            # .persist() is auto-called in new Chroma versions, but good to know
            print(f"✅ [Vector] Saved to {VECTOR_DB_DIR}")
        else:
            print("⚠️ [Vector] No documents to index!")

if __name__ == "__main__":
    builder = VectorStoreBuilder()
    builder.build()
import json
import os
import shutil
import ast
import gc
import time
import stat
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_core.documents import Document
from src.config import *
from src.model import shared_embeddings

MAX_CHUNK_SIZE = 3000 

class VectorStoreBuilder:
    def __init__(self):
        print(f"[Vector] => Loading Embedding Model: {MODEL_NAME}...")
        
        self.embeddings = shared_embeddings
        
        #python aware splitter for large files
        self.splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=MAX_CHUNK_SIZE,
            chunk_overlap=200
        )

        self.dependency_map = {}
        if os.path.exists(DEPENDENCY_MAP_FILE):
            with open(DEPENDENCY_MAP_FILE, "r") as f:
                self.dependency_map = json.load(f)

    def read_code(self, file_path, start_line, end_line):
        """Reads the exact lines from the source file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                start = max(0, start_line - 1)
                end = end_line
                return "".join(lines[start:end])
        except Exception as e:
            print(f"[Vector] => Could not read {file_path}: {e}")
            return ""

    def get_skeleton_code(self, code_content):
        """Extracts structure (imports, classes, defs) without function bodies."""
        
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
                    skeleton_lines.append("    # ... (Logic indexed in separate node) ...")
            
            return "\n".join(skeleton_lines)
        except:
            return code_content 

    def get_header(self, node):
        header = f"FILE: {node['file']}\n"
        header += f"ID: {node['id']}\n"
        header += f"TYPE: {node['type']}\n"
        
        if node['id'] in self.dependency_map:
            deps = self.dependency_map[node['id']][:5] 
            clean_deps = [d.split(".")[-1] for d in deps]
            header += f"USES: {', '.join(clean_deps)}\n"
        
        return header

    def force_delete_folder(self, folder_path):
        """ robust deletion for Windows file locks """
        if not os.path.exists(folder_path): return

        print(f"[Vector] => Clearing old DB at {folder_path}...")
        gc.collect()

        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        for i in range(5):
            try:
                shutil.rmtree(folder_path, onerror=remove_readonly)
                return 
            except PermissionError:
                time.sleep(1.0)
            except Exception:
                return

    def build(self):
        print('[Vector] => Started vector processing...')
        
        self.force_delete_folder(VECTOR_DB_DIR)
        
        if not os.path.exists(INPUT_FILE):
             print(f"[Vector] => No graph file found at {INPUT_FILE}")
             return

        with open(INPUT_FILE, "r") as f:
            data = json.load(f)
        
        documents = []
        for node in data["nodes"]:
            #accept functions, classes, and full modules
            if node["type"] not in ["function", "class", "module"]:
                continue

            #construct full path using config REPO_PATH (Safe Data Dir)
            full_path = os.path.join(REPO_PATH, node["file"])
            
            code_content = self.read_code(
                full_path, 
                node["start"], 
                node["end"]
            )
            
            if not code_content.strip(): continue

            #handle modules , functions
            if node["type"] == "module":
                final_content = self.get_skeleton_code(code_content)
                header = f"FILE_CONTEXT: {node['file']}\n(Contains Imports, Globals, and Script Logic)\n"
            else:
                final_content = code_content
                header = self.get_header(node)

            base_metadata = {
                "id": node["id"],
                "file": node["file"],
                "start_line": node["start"],
                "end_line": node["end"],
                "role": "container" if node["type"] == "module" else "logic",
                "node_type": node["type"],
              
            }
            
            # Chunking logic
            if len(final_content) > MAX_CHUNK_SIZE:
                chunks = self.splitter.split_text(final_content)
                for i, chunk in enumerate(chunks):
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
                doc = Document(
                    page_content=f"{header}\n--- FULL BODY ---\n{final_content}",
                    metadata={
                        **base_metadata,
                        "is_chunk": False,
                        "chunk_index": 0,
                        "total_chunks": 1
                    }
                )
                documents.append(doc)
                
        if documents:
            print(f"[Vector] => Embedding {len(documents)} documents...")
            vector_db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=VECTOR_DB_DIR,
                collection_name="codebase_v1"
            )
            #vector_db.persist() # New Chroma versions persist automatically
            del vector_db 
            gc.collect()
            print(f"[Vector] => Saved to {VECTOR_DB_DIR}")
        else:
            print("[Vector] => No documents to index!")
import json
import os
import shutil
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_core.documents import Document
import torch
 
 
INPUT_FILE = "semantic_graph_v2.json"
OUTPUT_DIR = "./storage"
DEPENDENCY_MAP_FILE = os.path.join(OUTPUT_DIR, "dependency_map.json")
VECTOR_DB_DIR = os.path.join(OUTPUT_DIR, "chroma_db")


MODEL_NAME = "jinaai/jina-embeddings-v2-base-code"
MAX_CHUNK_SIZE = 2000 

class VectorStoreBuilder:
    def __init__(self):
        print(f"[Vector] => Loading Embedding Model: {MODEL_NAME}...")
        
        self.device_type = 'cpu'
        
        #checking the gpu accessbility
        if torch.cuda.is_available():
            self.device_type = "cuda"
        
        print ('[vector] => Using ', self.device_type)
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=MODEL_NAME,
            model_kwargs={"device": self.device_type, "trust_remote_code": True}
        )
        
        #using python aware spliter for the larger functions
        self.splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=MAX_CHUNK_SIZE,
            chunk_overlap=200
        )

        #loading the dependacy_map we built in the graph
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
            print(f"[Vector] => not not read {file_path}: {e}")
            return ""
    
    def get_header(self, node):
        
        header = f"FILE: {node['file']}\n"
        header += f"ID: {node['id']}\n"
        header += f"TYPE: {node['type']}\n"
        
        #If the current node is calling the other node, then we enjecting the sub nodes.
        if node['id'] in self.dependency_map:
            deps = self.dependency_map[node['id']][:5] #Limit to 5
            clean_deps = [d.split(".")[-1] for d in deps] #Just node's names
            header += f"USES: {', '.join(clean_deps)}\n"
        
        return header

    
    def build(self):
        print ('[vector] => Started the vector processing...')
        
        #clean the old one.
        if os.path.exists(VECTOR_DB_DIR):
            shutil.rmtree(VECTOR_DB_DIR)
        
        with open(INPUT_FILE, "r") as f:
            data = json.load(f)
        
        documents = []
        for node in data["nodes"]:
            #Skipping external libraries or irrelevented
            if node["type"] not in ["function", "class"]:
                continue

            #finds the codes
            code_content = self.read_code(
                './temp_repo/' + node["file"], 
                node["start"], 
                node["end"]
            )
            
            if not code_content.strip(): continue
            # print(code_content)

            base_metadata = {
                "id": node["id"],
                "file": node["file"],
                "start_line": node["start"],
                "end_line": node["end"],
                "role": node.get("role", "code"),
                "complexity": node.get("complexity", 0)
            }
            
            header = self.get_header(node)
            
            
            #if it is the larger code...
            if len(code_content) > MAX_CHUNK_SIZE * 1.5:
                chunks = self.splitter.split_text(code_content)
                
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
                #small codes
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
                
        if documents:
            print(f"[Vector] => Embedding the {len(documents)} documents...")
            
            # Using Chroma db
            vector_db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=VECTOR_DB_DIR,
                collection_name="codebase_v1"
            )
            
            print(f"[Vector] => Saved to {VECTOR_DB_DIR}")
        else:
            print("[Vector] => No documents to index!")

if __name__ == "__main__":
    
    builder = VectorStoreBuilder()
    builder.build()
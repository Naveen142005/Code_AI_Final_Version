import torch
from transformers import AutoModel
from typing import List

class EmbeddingModel:
    def __init__(self, model_name: str = 'jinaai/jina-embeddings-v2-base-code') -> None:
        print(f"[Embedder] => Loading {model_name}...")
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f'[Embedder] => Using {self.device}')
        
        self.model = AutoModel.from_pretrained(
            model_name, trust_remote_code=True
        ).to(self.device).eval()
        
        print(f"Model loaded with {self.device}")

    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
    
        with torch.no_grad():
            return self.model.encode(texts).tolist()

    def embed_query(self, text: str) -> List[float]:
        
        with torch.no_grad():
            return self.model.encode([text])[0].tolist()

shared_embeddings = EmbeddingModel()
import pickle
from langchain_chroma import Chroma
from model import *
from config import *
import os

class ConceptSearchTool:
    def __init__(self):
        print (f'[ConceptSearcher] => Loading...')

        self.embeddings = shared_embeddings
        
        if os.path.exists(VECTOR_DB_DIR):
            self.vector_db = Chroma(
                persist_directory=VECTOR_DB_DIR,
                embedding_function=self.embeddings,
                collection_name='codebase_v1'
            )
        else:
            print (f'[ConceptSearcher] => No vector DB Found')
            self.vector_db = None
        
        if os.path.exists(BM25_PATH):
            with open(BM25_PATH, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["model"]
                self.bm25_nodes = data["node_map"]
        else:
            print("[ConceptSearcher] => BM25 Index not Found")
            self.bm25 = None
    
    def rank(self, vector_results, bm25_results, k = 60):
        """
        Merge two results based on the position and it's repeativeness
        """
        
        scores = {}
        
        for rank, docx in enumerate(vector_results):
            # print(docx)
            docx_id = docx.metadata['id']
            if docx_id not in scores: 
                scores[docx_id] = 0
            scores[docx_id] += 1 / (k + rank + 1)

        for rank, docx_id in enumerate(bm25_results):
            if docx_id not in scores: 
                scores[docx_id] = 0
            scores[docx_id] += 1 / (k + rank + 1)

            
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return sorted_ids

    
    def search(self, query, limit=5):
        if not query: return []
        print(f"[ConceptTool] => Searching for: '{query}'")
        
        vector_data = []
        
        if self.vector_db:
            vector_data = self.vector_db.search(query=query, search_type='mmr', k= limit+5)
            print (f'[ConceptTool] => {[d.metadata['id'] for d in vector_data]}')
        
        bm25_data = []
        if self.bm25:
            
            tokenized_query = query.lower().split() #simple split for now
            
            # get_top_n returns the text, we need the indices to map back to ids
            scores = self.bm25.get_scores(tokenized_query)
            #get top N indexes
            top_n_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit*2]
            #map index to Node ids
            bm25_data = [self.bm25_nodes[i] for i in top_n_indices if scores[i] > 0]
            
            print(f"[ConceptTool] => BM25 found: {bm25_data}")
        
        final_ranked_ids = self.rank(vector_data, bm25_data)
        
        #return top N
        return final_ranked_ids[:limit]

            

import re

from src._agents.file_reader import FileReader_
from src._agents.nodes.expand import expander


class Grader:
    def __init__(self):pass
        # print("[Grader] => Ready to rank candidates.")
        
        
    def _normalize(self, text: str) -> str:
        if not text: return ""
        return re.sub(r'\s+', '', text.lower())

    def _calculate_content_score(self, query: str, content: str) -> float:
        score = 0
        norm_query = self._normalize(query)
        norm_content = self._normalize(content)

        # 1. Exact Snippet Match (The "Smoking Gun")
        if norm_query in norm_content:
            score += 100
        
        # 2. Token Overlap (Partial Evidence)
        # If query is "nodes = data.get"
        # We check if 'nodes', 'data', 'get' exist near each other.
        q_tokens = re.findall(r"\w+", query.lower())
        content_lower = content.lower()
        
        matches = sum(1 for t in q_tokens if t in content_lower)
        if len(q_tokens) > 0:
            score += (matches / len(q_tokens)) * 20  # Up to 20 points for token overlap

        return score

    def _calculate_name_score(self, query: str, node_id: str) -> float:
        """
        SCENARIO 1 CHECK: Is the user asking for a function name?
        """
        score = 0
        leaf_name = node_id.split('.')[-1].lower()
        query_parts = query.lower().split()

        # 1. Exact Name Match (e.g. Query "add_var", Node "_add_var")
        if any(part == leaf_name for part in query_parts):
            score += 50
        
        # 2. Partial Name Match
        elif any(part in leaf_name for part in query_parts if len(part) > 3):
            score += 20
            
        return score

    def grade(self, query: str, candidates: list[str]) -> str:
        """
        The Main Entry Point.
        Accepts: Query string, List of candidate dicts {'id', 'content', 'metadata'}
        Returns: The single best Node ID.
        """
        # print(f"   ⚖️  Grading {len(candidates)} candidates for: '{query}'")
        
        # Detect if this is a "Code Search" (contains =, (, [, .)
        is_code_search = any(ch in query for ch in "=([.") and " " in query
        
        ranked_results = []

        for cand in candidates:
            node_id = cand
            
            content = FileReader_().read_file(node_id)
            # Start with 0
            final_score = 0
            
            # --- FACTOR 1: CONTENT EVIDENCE (Weights heavily if is_code_search) ---
            if is_code_search:
                final_score += self._calculate_content_score(query, content)
            
            # --- FACTOR 2: NAME EVIDENCE (Weights heavily for concept search) ---
            final_score += self._calculate_name_score(query, node_id)
            
            # --- FACTOR 3: PATH PENALTY (Tie-Breaker) ---
            # Penalize deep files or tests slightly (-0.5 per folder depth)
            depth = node_id.count('/')
            final_score -= depth * 0.5

            ranked_results.append((final_score, node_id))
            print(f"      - {node_id} -> Score: {final_score:.1f}")

        # Sort by score (Highest first)
        ranked_results.sort(key=lambda x: x[0], reverse=True)
        
        best_match = ranked_results[0]
        # print(f"   🏆 Winner: {best_match[1]} (Score: {best_match[0]:.1f})")
        
        return best_match[1]

from src._agents.nodes.expand import expander
from src._agents.nodes.final import Presenter
from src._agents.nodes.grader import Grader
from src._agents.nodes.retriver import retriver
from src._agents.nodes.router import Router
from src._agents.state import AgentState
from src.start import Main
from src.store.bm25 import BM25Builder
from src.store.graph import GraphBuilder
from src.store.vector import VectorStoreBuilder



def repo_loader(state: AgentState) -> AgentState:
    """Load repository and start ingestion"""
    repo_url = state.get('input', '')
    if not repo_url:
        repo_url = input('[Repo Loader] => Enter GitHub URL: ').strip()
    
    start = Main()
    start.main(repo_url)
    
    return {'input': repo_url}


def build_vector(state: AgentState) -> AgentState:
    """Build vector store"""
    print("[Vector Store] Building...")
    builder = VectorStoreBuilder()
    builder.build()
    return {}


def build_bm25(state: AgentState) -> AgentState:
    """Build BM25 index"""
    print("[BM25] Building...")
    builder = BM25Builder()
    builder.build()
    return {}


def build_graph(state: AgentState) -> AgentState:
    """Build dependency graph"""
    print("[Graph] Building...")
    builder = GraphBuilder()
    builder.build()
    return {}


def router_node(state: AgentState) -> AgentState:
    """Route query to CODE or CHAT path"""
    query = state.get('query', '')
    is_code = Router().route(query)
    return {'chat': is_code}  #True = CODE, False = CHAT


def retriver_node(state: AgentState) -> AgentState:
    """Retrieve relevant code blocks"""
    query = state.get('query', '')
    results = retriver().search(query)
    return {'research_results': results}


def grader_node(state: AgentState) -> AgentState:
    """Grade search results and select best match"""
    query = state.get('query', '')
    results = state.get('research_results', [])
    
    grader_result = Grader().grade(query, results)
    #grader_result = (is_ok, index, reason)
    
    is_ok = grader_result[0]
    
    return {
        'resolved_query': grader_result,
        'is_ok': is_ok
    }


def expander_node(state: AgentState) -> AgentState:
    """Expand code context with parents and children"""
    resolved = state.get('resolved_query', [])
    results = state.get('research_results', [])
    
    idx = resolved[1]  
    node_id = results[idx] - 1
    
    expanded = expander().expand(node_id)
    return {'prompt_final': expanded['formatted_explanation']}


def presenter_node(state: AgentState) -> AgentState:
    """Generate final explanation"""
    query = state.get('query', '')
    
    
    prompt = state.get('prompt_final', '')
    
    if prompt:
        # CODE path with context
        response = Presenter().final(query, prompt)
    else:
        # CHAT path without context
        response = Presenter().final(query, "")
    
    return {'final_response': response}


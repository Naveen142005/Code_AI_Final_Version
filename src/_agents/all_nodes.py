
from src._agents.architect_node.FlowDiagram import FlowDiagramGenerator
from src._agents.nodes.expand import expander
from src._agents.nodes.final import Presenter
from src._agents.nodes.general import GeneralAssistant
from src._agents.nodes.grader import Grader
from src._agents.nodes.retriver import retriver

from src._agents.nodes.router import Router
from src._agents.state import AgentState
from src.ingestion.repo_loader import RepoLoader
from src.store.bm25 import BM25Builder
from src.store.graph import GraphBuilder
from src.store.vector import VectorStoreBuilder
from src.temp import ProjectSummarizer


def repo_loader(state: AgentState) -> AgentState:
    """Load repository and start ingestion"""
    repo_url = state.get('input', '')
    print ("Repo Url => " ,repo_url)

    if repo_url:
        start = RepoLoader()
        start.load(repo_url)
    
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
    res = Router().route(query)
   
    return {'router_response': res}  

def retriver_node(state: AgentState) -> AgentState:
    """Retrieve relevant code blocks"""
    query = state.get('query', '')
    print('query ======>', query)
    results = retriver().search(query)
    print('-' * 70)
    print('resuls' , results)
    return {'research_results': results}


def grader_node(state: AgentState) -> AgentState:
    """Grade search results and select best match"""
    query = state.get('query', '')
    results = state.get('research_results', [])
    
    grader_result = Grader().grade(query, results)
    #grader_result = (is_expendable, index, reason)
    print ('grader result -> ', grader_result)
    is_expendable = grader_result[0]
    
    return {
        'resolved_query': grader_result,
        'is_expendable': is_expendable
    }


def expander_node(state: AgentState) -> AgentState:
    """Expand code context with parents and children"""
    resolved = state.get('resolved_query', [])
    results = state.get('research_results', [])
    
    idx = resolved[1]
    print('idx =>', idx) 
    print ('type ->' , type(idx))
    node_id = results[idx[0] - 1]
    
    expanded = expander().expand(node_id)
    return {'explanation_prompt': expanded['formatted_explanation']}


def presenter_node(state: AgentState) -> AgentState:
    """Generate final explanation"""
    query = state.get('query', '')
    
    router_response = state.get('router_response')
    
    if router_response == "CODE":
        is_expendable = state.get('is_expendable')
        if is_expendable:
            prompt = state.get('explanation_prompt', '')
            response = Presenter().explanation_response(query, prompt)
        else:
            ans = state.get('resolved_query')
            response = ans[2] 
    else:
        prompt = state.get('overview_prompt', '')
        response = Presenter().overview_response(prompt)
        
    
    return {'final_response': response}

def general_assistant_node(state: AgentState) -> AgentState:
    """Node for handling CHAT interactions (Hi, Hello, General questions)."""
    query = state.get('query', '')
    
    assistant = GeneralAssistant()
    response = assistant.respond(query)
    
    return {'final_response': response}

def architecture_node(state: AgentState) -> AgentState:
    query = state.get('query', '')
    router_response = state.get('router_response', '')
    
    if router_response == 'PROJECT':
        summarizer = ProjectSummarizer()
        context = summarizer.get_context()
        return {'overview_prompt': context}
    else:
        generator = FlowDiagramGenerator()
        prompt = generator.generate_prompt()
        return {'overview_prompt': prompt}


    
    
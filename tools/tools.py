from langchain_core.tools import tool

from tools.conceptseacher import ConceptSearchTool
from tools.diagramgenertor import DiagramGenerator
from tools.exact_matcher import ExactMatchTool
from tools.filereader import FileReader
from tools.graphseacher import GraphSearchTool
from tools.projectoverviewer import ProjectOverViewTool



#Concept Search Tool
@tool
def concept_search_tool(queries: list[str]):
    """
    Performs a Hybrid Search (Semantic + Keyword) to find relevant code concepts.
    Use this when:
    - You need to understand how a feature works (e.g., "How does login work?").
    - You are looking for code logic but don't know the file name.
    
    Args:
        queries: A list of search strings (e.g., ["retry logic", "payment failure"]).
                 Usually just one query is enough.
    """
    
    combined_query = " ".join(queries)
    return Concept_searching_tool.search(combined_query, limit=5)


#File read tool
@tool
def read_file_tool(file_path: str, start_line: int = 1, end_line: int = None):
    """
    Reads code from a specific file.file_path must be a string.
    ALWAYS use this when you need to see the implementation details, fix bugs, or explain logic.
    
    Args:
        file_path: Relative path to the file (e.g., 'src/utils.py')
        start_line: (Optional) Line number to start reading from.
        end_line: (Optional) Line number to stop reading at.
    """
    return file_reader.read_file(file_path, start_line, end_line)


@tool
def list_files_tool():
    """
    Lists the file structure of the project.
    Use this when:
    1. You want to explore the project layout.
    2. You are not sure about the exact file name.
    """
    return file_reader.list_files()



@tool
def structure_inspector_tool(node_id: str):
    """
    Inspects the structure of a code object (Function/Class).
    Use this to find:
    - Who calls this function? (Callers)
    - What does this function call? (Dependencies)
    - Parent Classes (Inheritance)
    - Where is it defined? (File path)
    
    Args:
        node_id: The exact ID of the node (e.g., 'auth.login_user' or 'file::src/main.py')
    """
    
    # Get basic connections
    data = graph_search_tool.get_node(node_id)
    
    # get Inheritance (if it's a class)
    if isinstance(data, dict):
        inheritance = graph_search_tool.get_inheritance(node_id)
        if inheritance:
            data["inherits_from"] = inheritance

    return f"Structure Data: {data}"



@tool
def diagram_generator_tool(node_ids: list[str], depth: int = 1):
    """
    Generates a Mermaid.js diagram for specific parts of the codebase.
    Use this when the user asks to "Visualize", "Draw", or "Show the architecture".
    
    Args:
        node_ids: A list of Node IDs to center the diagram around (e.g., ['auth,login']).
        depth: How many levels of neighbors to include. (Default: 1).
               Keep small (1 or 2) to avoid messy diagrams.
    """
    
    return diagram_tool.generate(node_ids, depth)


@tool
def symbol_lookup_tool(symbol_name: str):
    """
    Finds the exact definition file and line for a specific variable, function, or class name.
    Use this when the user asks "Where is X defined?" or "Find usages of Y".
    
    Args:
        symbol_name: The exact name to look for (e.g., 'MAX_RETRY', 'User', 'process_data')
    """
    return exact_matcher_tool.lookup(symbol_name)


@tool
def project_outline_tool():
    """
    Returns a high-level summary of the project.
    Includes:
    1. The 'README' content (dynamically found).
    2. The Top 8 most important files (Gravity Score).
    3. The File Directory Tree.
    
    Use this for questions like "Explain this project", "What does this repo do?", 
    or "What is the architecture?".
    """
    return project_overview_tool.generate_outline()


exact_matcher_tool = ExactMatchTool()
project_overview_tool = ProjectOverViewTool()
diagram_tool = DiagramGenerator()
graph_search_tool = GraphSearchTool()
Concept_searching_tool = ConceptSearchTool()
file_reader = FileReader()

TOOL_MAPPING = {
    "ConceptSearch": [concept_search_tool],
    "StructureInspector": [structure_inspector_tool],
    "FileReader": [read_file_tool, list_files_tool],
    "DiagramGenerator": [diagram_generator_tool],
    "SymbolTracker": [symbol_lookup_tool],
    "ProjectOutline": [project_outline_tool],
    "GeneralChat": [] 
}

def get_tools_by_name(tool_names: list[str]):
    
    active_tools = []
    for name in tool_names:
        tools = TOOL_MAPPING.get(name, [])
        active_tools.extend(tools)
    
    unique_tools_map = {tool.name: tool for tool in active_tools}
    
    return list(unique_tools_map.values())
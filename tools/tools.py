from langchain_core.tools import tool
from conceptseacher import ConceptSearchTool
from filereader import FileReader
from diagramgenertor import DiagramGenerator
from projectoverviewer import ProjectOverViewTool
from graphseacher import GraphSearchTool


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


@tool
def read_file_tool(file_path: str, start_line: int = 1, end_line: int = None):
    """
    Reads code from a specific file. 
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


Concept_searching_tool = ConceptSearchTool()
file_reader = FileReader()
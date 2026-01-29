import json
from langchain_core.messages import SystemMessage, HumanMessage
from src._agents.architect_node.diagram import DiagramGenerator
from src._agents.architect_node.graph_analyzer import GraphAnalyzer
from src._agents.architect_node.presenter import ArchitectPresenter
from src.config import llm
from src._agents.state import AgentState

class QueryClassifier:
    def __init__(self):
        pass

    def classify(self, query: str):
        print(f"[Architect] => Classifying Intent for: '{query}'")
        
        system_prompt = f"""
[ Query : {query} ]

You are a query classifier for a codebase analysis system.

Classify the user's query into ONE of these architect types:

1. overview: General project explanation, architecture
2. flow: Execution flow, process visualization
3. core_modules: Important components, key files
4. entry_points: Where to start, how to run
5. function_flow: Flow of a specific function

OUTPUT FORMAT:
Return ONLY a raw JSON object.

Here is the output schema:
{{
  "title": "ArchitectClassification",
  "type": "object",
  "properties": {{
    "architect_type": {{
      "title": "Architect Type",
      "description": "One of: overview, flow, core_modules, entry_points, function_flow",
      "type": "string"
    }},
    "scope": {{
      "title": "Scope",
      "description": "One of: project, module, function",
      "type": "string"
    }},
    "needs_diagram": {{
      "title": "Needs Diagram",
      "description": "Whether a visual diagram would help explain the answer",
      "type": "boolean"
    }},
    "target_entity": {{
      "title": "Target Entity",
      "anyOf": [
        {{ "type": "string" }},
        {{ "type": "null" }}
      ]
    }},
    "reasoning": {{ 
      "title": "Reasoning",
      "type": "string"
    }}
  }},
  "required": [
    "architect_type",
    "scope",
    "needs_diagram",
    "target_entity",
    "reasoning"
  ]
}}
Think step by step:
1. What is the user asking for?
2. Is it about the whole project or a specific part?
3. Would a diagram help visualize the answer?
4. Are they asking about a specific function/file?"""

        try:
            
            response = llm.invoke([
                SystemMessage(content=system_prompt)
            ])
            
            content = response.content.strip()
            
            if "```" in content:
                 content = content.split("```")[1].replace("json", "").strip()
            
            data = json.loads(content)
            
            print(f"[Architect] => Classified as: {data.get('architect_type')}")
            return data
            
        except Exception as e:
            print(f"[Architect] => Classification Error: {e}")
            
            return {
                'architect_type': 'overview',
                'scope': 'project', 
                'needs_diagram': True, 
                'target_entity': None,
                'reasoning': "Fallback due to classification error"
            }

import sys
import os

if __name__ == "__main__":
    
    test_queries = [
        "What does this project do?",               
        "Show me the execution flow of the system", 
        "What are the core modules?",               
        "Where should I start?",                    
        "Explain the flow of build()",              
    ]

    # print("\n====== ARCHITECT PATH END-TO-END TEST ======\n")

    
    classifier = QueryClassifier()
    
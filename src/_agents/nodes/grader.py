import json
import re

from src._agents.file_reader import FileReader_
from src._agents.nodes.expand import expander
from src.config import llm
from langchain_core.messages import SystemMessage, HumanMessage

class Grader:
    def __init__(self):
        pass
    
    def grade(self, query: str, candidates: list[str]) -> str:
        
        system_prompt ="""You are a code selection assistant. Return ONLY raw JSON - no text, no markdown, no explanations.
Output Format
json{"ok": boolean, "index": [integers], "reason": "string"}
Rules:

ok: true → exactly ONE index, reason is ""
ok: false with multiple indices → provide disambiguation in reason
ok: false with empty array [] → explain what wasn't found

Code Block Structure
Each block has:

Index: Number (1, 2, 3...)
Id: folder/file.ClassName.method_name (90% of time)

Variations: Store_/vector = store/vector (normalize case/separators)
Class-only: store/vector.VectorStoreBuilder (no method)
Method-specific: store/vector.VectorStoreBuilder.build (has method)


Code: Actual lines showing function definitions

Critical Selection Rules
ALWAYS verify both Id AND actual code:

Method-specific Id (e.g., .build) + code shows def build( → STRONG MATCH ✅
Class-only Id (no method name) + code shows requested function → WEAK MATCH
Class-only Id + code does NOT show requested function → NO MATCH ❌

Example:

Query: "explain the build function in vector class"
Index 1: Id=store/vector.VectorStoreBuilder, Code shows def __init__, def read_code → NO MATCH (no build visible)
Index 2: Id=store/vector.VectorStoreBuilder.build, Code shows def build(self): → MATCH ✅

Selection Process

Parse query: Extract function name, class context, fuzzy variations (e.g., "add var" = _add_var)
For each block:

Parse Id components (normalize case/separators)
Check if code contains def function_name(
Match against query (function name + class context if specified)


Decide:

One clear match → {"ok": true, "index": [N], "reason": ""}
Multiple matches → {"ok": false, "index": [N1,N2], "reason": "Multiple 'X' found:\n1. [Index N1] id.here\n2. [Index N2] id.here\n\nWhich one?"}
No match → {"ok": false, "index": [], "reason": "Function 'X' not found"}



Key Cases
Class context specified: Filter by class name first

Query: "build in vector class" → only match classes containing "vector"

Private vs public: _add_var ≠ add_var (different functions)
Same function, different classes: Disambiguate unless query specifies class
Fuzzy matching: "add var" matches _add_var, add_variable
Examples
Query: "explain the build function in vector class"
json{"ok": true, "index": [2], "reason": ""}
Query: "explain the build function" (ambiguous)
json{"ok": false, "index": [2, 5], "reason": "Multiple 'build' functions found:\n1. [Index 2] store/vector.VectorStoreBuilder.build\n2. [Index 5] store/graph.GraphBuilder.build\n\nWhich one do you want explained?"}
RETURN ONLY RAW JSON. NO OTHER TEXT."""
        index = 0
        my_prompt = f"""   
                Query: {query}
                
                ===================================================================================================
                
                """
                
        for cand in candidates:
            node_id = cand
            
            content = FileReader_().read_file(node_id)[:1500]
            
            my_prompt += f"""
[ Index: {index + 1} , Id: {node_id}],

{content}
            =========================================================================================================
            """
            index += 1
            

        # print(my_prompt)
        response= ''
        try:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=my_prompt)
            ]
            )
        except Exception as e:
            print(e)
        
        # print("LLM answer = " , response.content)
        
        
        
        if response:
            # Check if response is already a string or has .content attribute
            if isinstance(response, str):
                response_content = response
            else:
                response_content = response.content if hasattr(response, 'content') else str(response)
        else:
            response_content = None

        # print("LLM answer =", response_content)

        # Parse and extract values
        ok = False
        index = []
        reason = ""

        if response_content:
            try:
                # Clean response in case of markdown formatting
                content = response_content.strip()
                
                # Remove markdown code fences if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                    content = content.strip()
                
                # Parse JSON
                result = json.loads(content)
                
                # Extract values with validation
                ok = result.get("ok", False)
                index = result.get("index", [])
                reason = result.get("reason", "")
                
                # print(f"ok = {ok}")
                # print(f"index = {index}")
                # print(f"reason = {reason}")
                
            except json.JSONDecodeError as e:
                # print(f"JSON parsing error: {e}")
                # print(f"Raw content: {content}")
                ok = False
                index = []
                reason = "Invalid JSON response from LLM"
                
            except Exception as e:
                # print(f"Unexpected error: {e}")
                ok = False
                index = []
                reason = str(e)
        
        return [ok, index, reason]
        
            
            
            
    
            
            
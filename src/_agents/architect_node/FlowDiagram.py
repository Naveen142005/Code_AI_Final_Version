import os
from src._agents.nodes.expand import expander
from src.config import REPO_PATH
import networkx as nx
import networkx as nx
import json
import os
from src._agents.nodes.expand import expander
from src.config import REPO_PATH, DEPENDENCY_MAP_FILE, llm

def find_entry_point(repo_path):
    repo_path = os.path.abspath(repo_path)

    common_names = ["main.py", "app.py", "run.py", "manage.py", "start.py", "cli.py"]
    for name in common_names:
        full_path = os.path.join(repo_path, name)
        if os.path.exists(full_path):
            return os.path.relpath(full_path, repo_path) 
    
    for root, _, files in os.walk(repo_path):
        
        if any(x in root for x in ["venv", "env", "tests", "node_modules", ".git"]): 
            continue

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        if 'if __name__' in f.read():
                            return os.path.relpath(full_path, repo_path) 
                except:
                    continue

    return None

class FlowDiagramGenerator:
    def __init__(self):
        self.graph = expander().get_graph()
        self.repo_root = os.path.abspath(REPO_PATH).lower()
        self.visited = set()
        
        self.dependency_map = {}
        if os.path.exists(DEPENDENCY_MAP_FILE):
            with open(DEPENDENCY_MAP_FILE, "r") as f:
                self.dependency_map = json.load(f)

        self.my_functions = set()
        self.get_my_functions()

    def get_my_functions(self):
        """Function for get the user defined function"""
        for key, values in self.dependency_map.items():
            
            if key.startswith("file."):
                for func_name in values:
                    self.my_functions.add(func_name)
                    
            self.my_functions.add(key)
        
        for i in self.my_functions:
            print(i)
            
        print(f" {len(self.my_functions)} user-defined functions.")

    def get_entry_point(self, file_path):
        """Finds the starting node """
        
        filename = os.path.basename(file_path)
        clean_name = os.path.splitext(filename)[0]
        
        module_node = None
        for node in self.graph.nodes:
            if f"file.{clean_name}" in str(node):
                module_node = node
                break
        
        if not module_node: return None

        children = self.dependency_map.get(module_node, [])
        for child in children:
            if str(child).lower().endswith(".main") or str(child).lower().endswith(".run"):
                return child
        
        return module_node

    def is_my_function(self, node_id):
        return node_id in self.my_functions

    def trace_flow(self, start_node, depth=0):
        """Getting the children names using DFS"""
        
        #for safty 
        if depth > 10: return [] 
    
        if start_node in self.visited: return []
        
        #set to track the traversing node
        self.visited.add(start_node)
        
        #taking the answers
        ans = []
        
        #getting all the chilren belongs to the node
        children = self.dependency_map.get(start_node, [])

        #Fall back.
        if not children and start_node in self.graph:
            children = list(self.graph.successors(start_node))

        #Filtering the user function only
        curr_childs = []
        for child in children:
            if self.is_my_function(child) and child != start_node:
                curr_childs.append(child)
        
        #alphabhet sorting for better understanding,
        curr_childs = sorted(list(set(curr_childs)), key=lambda x: str(x))

        if curr_childs:

            parent_func_name = start_node.split('.')[-1]
            child_func_name = [c.split('.')[-1] for c in curr_childs]
            
            #Getting the answer -> [a -> b, c]    
            line = f"Function **{parent_func_name}** calls -> {', '.join(child_func_name)}"
            ans.append(line)
            
            for child in curr_childs:
                #extend for storing the child nodes' child [a -> b,c  b -> c,d]
                ans.extend(self.trace_flow(child, depth + 1))
        
        return ans #returning as the answer list

    def generate_prompt(self):
        start_file = find_entry_point(REPO_PATH)
        if not start_file: return "Error: No entry point file found."
            
        start_node = self.get_entry_point(start_file)
        if not start_node: return f" Error: Could not map '{start_file}' to graph."

        print(f"tracing Flow from: {start_node}")

        self.visited.clear()
        flow_lines = self.trace_flow(start_node)
        
        final =  "\n".join(flow_lines)
        return f"""You are an expert software architect and Mermaid.js flowchart generator.

Your task has TWO parts:
1. Generate a professional Mermaid.js flowchart
2. Provide a clear explanation of the execution flow

═══════════════════════════════════════════════════════════════════════════════
PART 1: MERMAID DIAGRAM GENERATION
═══════════════════════════════════════════════════════════════════════════════

INPUT FORMAT:
Function **FunctionName** calls -> function1, function2, function3

ALGORITHM:

STEP 1: PARSE INPUT
- Extract caller from "Function **X**"
- Extract callees from "calls -> A, B, C"

STEP 2: BUILD NODE REGISTRY
- Collect ALL unique function names
- Assign sequential IDs: A, B, C, D, E, F...
- Each function gets exactly ONE node ID (no duplicates)

STEP 3: CREATE EDGES
- For each "calls" relationship: CallerID --> CalleeID
- If multiple functions call same target, show ALL arrows to that one node

STEP 4: APPLY STYLING
- Identify entry point (first function OR "main"/"start"/"app"/"run")
- Highlight with green color

OUTPUT FORMAT:
```mermaid
graph TD
    A[functionName1] --> B[functionName2]
    A --> C[functionName3]
    B --> D[functionName4]
    
    classDef entryPoint fill:#4CAF50,stroke:#333,stroke-width:4px
    class A entryPoint
```

═══════════════════════════════════════════════════════════════════════════════
PART 2: FLOW EXPLANATION
═══════════════════════════════════════════════════════════════════════════════

After the Mermaid diagram, provide a structured explanation:

## 🔄 Execution Flow Explanation

### Entry Point
- **Starting Function:** [name of entry function]
- **Location:** [file if known, or "main entry point"]
- **Purpose:** [what this function initiates]

### Flow Overview
[2-3 sentences explaining the high-level execution pattern]

### Execution Layers

**Layer 0 - Entry:**
- `[function_name]` - [what it does]

**Layer 1 - Initialization/Setup:**
- `[function_name]` - [what it does]
- `[function_name]` - [what it does]

**Layer 2 - Core Logic:**
- `[function_name]` - [what it does]
- `[function_name]` - [what it does]

**Layer N - Utilities/Helpers:**
- `[function_name]` - [what it does]

### Key Observations
- **Shared Dependencies:** [list any functions called by multiple parents]
- **Recursive Calls:** [note if any function calls itself or creates cycles]
- **Critical Path:** [identify the main execution sequence]

### Flow Pattern
[Identify the pattern: Linear, Branching, Event-Driven, Recursive, etc.]

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE OUTPUT
═══════════════════════════════════════════════════════════════════════════════

INPUT:
Function **main** calls -> init, process
Function **init** calls -> loadConfig
Function **process** calls -> validate, execute
Function **validate** calls -> check
Function **execute** calls -> check

EXPECTED OUTPUT:
```mermaid
graph TD
    A[main] --> B[init]
    A --> C[process]
    B --> D[loadConfig]
    C --> E[validate]
    C --> F[execute]
    E --> G[check]
    F --> G
    
    classDef entryPoint fill:#4CAF50,stroke:#333,stroke-width:4px
    class A entryPoint
```

## 🔄 Execution Flow Explanation

### Entry Point
- **Starting Function:** main
- **Location:** Main entry point
- **Purpose:** Orchestrates the application initialization and core processing

### Flow Overview
The application follows a sequential initialization pattern where the main function first sets up the configuration, then processes data through validation and execution phases. Both validation and execution converge on a shared check function, indicating a common verification step.

### Execution Layers

**Layer 0 - Entry:**
- `main` - Application entry point that coordinates initialization and processing

**Layer 1 - Initialization & Processing:**
- `init` - Handles application setup and configuration loading
- `process` - Manages the core data processing workflow

**Layer 2 - Configuration & Validation:**
- `loadConfig` - Loads application configuration from files
- `validate` - Validates processed data before execution
- `execute` - Executes the main business logic

**Layer 3 - Utilities:**
- `check` - Shared verification function used by both validate and execute

### Key Observations
- **Shared Dependencies:** The `check` function is called by both `validate` and `execute`, indicating a common verification step
- **Recursive Calls:** None detected
- **Critical Path:** main → process → validate → check (or execute → check)

### Flow Pattern
**Sequential Orchestrator** - The main function orchestrates sequential operations with a branching validation/execution phase that converges on shared utility functions.

═══════════════════════════════════════════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════════════════════════════════════════

Process this function call data:

{final}

═══════════════════════════════════════════════════════════════════════════════
OUTPUT REQUIREMENTS
═══════════════════════════════════════════════════════════════════════════════

1. First, output the Mermaid diagram
2. Then, output the flow explanation
3. Ensure the explanation accurately reflects the diagram
4. Be specific about function purposes (infer from names if needed)
5. Identify patterns and relationships clearly

Generate both the diagram and explanation now.
""" 

    
    
    
    
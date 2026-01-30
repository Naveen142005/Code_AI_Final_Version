import json
import os
import tempfile

# ==============================================================================
# 1. SETUP: CREATE DUMMY DATA & CONFIG (Simulating your environment)
# ==============================================================================

# Create a temporary directory for the test
temp_dir = tempfile.mkdtemp()
DATA_CACHE_DIR = temp_dir
FLOW_FILE = os.path.join(DATA_CACHE_DIR, "flow_intelligence.json")


# Save this dummy data to the temp file
with open(FLOW_FILE, "w") as f:
    json.dump(dummy_flow_data, f)

print(f"✅ Setup: Created mock flow data at {FLOW_FILE}")

# ==============================================================================
# 2. THE TOOL: PROJECT OVERVIEWER (Your Code)
# ==============================================================================

class ProjectOverviewer:
    def __init__(self):
        self.data = None
        if os.path.exists(FLOW_FILE):
            with open(FLOW_FILE, "r") as f:
                self.data = json.load(f)

    def get_summary(self):
        if not self.data:
            return "Error: Architecture map not found."

        # 1. GET ENTRY POINT
        entry = self.data.get("entry_point", "Unknown")
        file_path = self.data.get("entry_point_file", "unknown file")
        
        # 2. FORMAT THE FLOW
        layers = self.data.get("flow_layers", {})
        narrative = ""
        sorted_depths = sorted(layers.keys(), key=int)
        
        for depth in sorted_depths:
            nodes = layers[depth]
            visible = ", ".join([f"`{n.split('.')[-1]}`" for n in nodes[:4]]) 
            if len(nodes) > 4: visible += f" (+{len(nodes)-4} more)"
            narrative += f"STEP {depth}: {visible}\n"

        # 3. FORMAT THE ORPHANS (Subsystems)
        orphans = self.data.get("orphaned_modules", {})
        subsystems = ""
        if orphans:
            subsystems = "\nMAJOR SUBSYSTEMS DETECTED (Likely called dynamically):\n"
            for category, nodes in orphans.items():
                clean_nodes = [n.split('.')[-1] for n in nodes[:2]] 
                subsystems += f"- **{category.upper()}**: {', '.join(clean_nodes)}\n"

        # 4. FINAL CONTEXT
        return f"""
PROJECT ARCHITECTURE REPORT
---------------------------
🚀 START HERE: {entry}
📂 FILE: {file_path}

🌊 EXECUTION FLOW (Explicit Calls):
{narrative}
{subsystems}
---------------------------
"""

# ==============================================================================
# 3. THE SIMULATION: MOCK LLM & AGENT LOGIC
# ==============================================================================

def mock_llm_response(prompt):
    """
    Simulates what a real LLM (like GPT-4 or Gemini) would say 
    given the prompt generated above.
    """
    print("\n🤖 [LLM] Generating Answer based on the report...\n")
    
    # This is a hardcoded string simulating the AI interpreting your data
    return f"""
Here is the complete flow of the project:

### 🚀 Where to Start
You should begin by looking at **`src/start.py`**. The entry point function is **`Main.main`**.

### 🌊 The Execution Flow
1.  **Initialization:** The `Main.main` function starts the process.
2.  **Ingestion:** It immediately triggers the `RepoLoader` to load your files and calls `analyze_codebase` to begin processing.
3.  **Indexing:** The analyzer then hands off work to the `SemanticIndexer` to walk through the code structure.

### 🏗️ Major Subsystems
Beyond the main flow, the system relies on several critical components for data storage and AI processing:
* **Vector Store:** Managed by `VectorStoreBuilder` (likely for embeddings).
* **Graph:** Managed by `GraphBuilder` (likely for dependency mapping).
* **Agents:** The system uses `router_node` and `retriver_node` to handle queries.
    """

# ==============================================================================
# 4. EXECUTION: RUN THE SCENARIO
# ==============================================================================

if __name__ == "__main__":
    print("==================================================")
    print("🧪 TEST SCENARIO: 'Explain the entire flow'")
    print("==================================================")
    
    # 1. Instantiate the Tool
    tool = ProjectOverviewer()
    
    # 2. Get the Context (The prompt data)
    context = tool.get_summary()
    
    print("\n🔹 [TOOL OUTPUT] Generated Context for LLM:")
    print(context)
    print("-" * 50)
    
    # 3. Simulate the Final User Answer
    final_answer = mock_llm_response(context)
    
    print("🔹 [FINAL ANSWER] What the user sees:")
    print(final_answer)
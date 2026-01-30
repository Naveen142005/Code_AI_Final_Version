import os
import ast
from src._agents.architect_node.presenter import find_entry_point
from src.config import REPO_PATH, llm


class ProjectSummarizer:
    def __init__(self):
        self.repo_path = os.path.abspath(REPO_PATH)

    def get_context(self):

        readme_candidates = ["README.md", "README.txt", "readme.md"]
        for name in readme_candidates:
            path = os.path.join(self.repo_path, name)
            if os.path.exists(path):
                print(f"Found Documentation: {name}")
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    return f"PROJECT DOCUMENTATION (from {name}):\n\n" + f.read()[:2000] 

        print("No, can't README found. Generating own analysis...")
        return self.get_summary()

    def get_summary(self):
        
        """
        Scans code to guess what the project does.
        """
        
        start_file = find_entry_point(self.repo_path)
        if not start_file:
            return "Project Analysis Failed: No Entry Point found."

        full_start_path = os.path.join(self.repo_path, start_file)
        
        
        imports = self.get_from_imports(full_start_path)
        tech_stack = ", ".join(imports) if imports else "Standard Python"
        
        docstring = self.doc_string(full_start_path)

        
        files_names = self.file_names()

        return f"""
PROJECT AUTO-ANALYSIS (No README Found)
---------------------------------------
1. **Entry Point:** `{start_file}`
2. **Tech Stack:** {tech_stack} (Detected from imports)
3. **Key Modules:** {', '.join(files_names)}
4. **Developer Description:** "{docstring}"
"""

    def get_from_imports(self, file_path):
        """Extracts top-level imports for identify."""
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read())
            
            libs = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        libs.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        libs.add(node.module.split('.')[0])
            
            
            stdlib = {'os', 'sys', 'json', 'time', 'math', 'random', 're', 'collections'}
            return list(libs - stdlib)
        except:
            return []

    def doc_string(self, file_path):
        """Reads the very first comment/docstring in the file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read())
            return ast.get_docstring(tree) or "No description provided in code."
        except:
            return "Could not read file."

    def file_names(self):
        """Returns the 5 largest python files (likely the core logic)."""
        file_sizes = []
        for root, _, files in os.walk(self.repo_path):
            for f in files:
                if f.endswith(".py") and "venv" not in root:
                    path = os.path.join(root, f)
                    size = os.path.getsize(path)
                    file_sizes.append((f, size))
        
        
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in file_sizes[:5]]




if __name__ == "__main__":
    summarizer = ProjectSummarizer()
    context = summarizer.get_context()
    
    print("\n" + "="*60)
    print("🤖 AI PROMPT: 'WHAT DOES THIS PROJECT DO?'")
    print("="*60)
    print(f"Here is the context about the project:\n{context}")
    print("="*60)
    
    prompt = f"""You are a senior software architect with expertise in explaining complex codebases clearly and concisely.

═══════════════════════════════════════════════════════════════════════════════
CONTEXT PROVIDED
═══════════════════════════════════════════════════════════════════════════════

{context}

═══════════════════════════════════════════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════════════════════════════════════════

Explain what this project does in a clear, structured format that answers:

1. **What is this project?** (1-2 sentence summary)
2. **What problem does it solve?** (The "why")
3. **How does it work?** (High-level architecture)
4. **Key technologies used** (Tech stack)
5. **Main components/modules** (Core building blocks)

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════════════

Use this exact structure:

---

## 📋 Project Overview

**What it is:**
[1-2 sentence description of what this application does]

**Purpose:**
[Why this project exists - what problem it solves]

---

## 🏗️ Architecture

**Type:** [e.g., Web Application, CLI Tool, API Service, Desktop App, Library]

**How it works:**
[3-4 sentences explaining the high-level flow]

**Entry Point:**
- File: `[entry_file_name]`
- Function: `[main function if known]`

---

## ⚙️ Core Components

1. **[Component 1 Name]**
   - Purpose: [What it does]
   - Key files: [file names]

2. **[Component 2 Name]**
   - Purpose: [What it does]
   - Key files: [file names]

[Continue for 3-5 main components]

---

## 🔧 Tech Stack

- **Language:** Python [version if known]
- **Frameworks:** [Flask/Django/FastAPI/etc or "None - Pure Python"]
- **Key Libraries:** [list important dependencies]
- **Database:** [if applicable]
- **Other:** [any other notable tech]

---

## 🚀 Getting Started

**To run this project:**
1. [Step 1 based on entry point]
2. [Step 2 if configuration needed]
3. [Step 3 to execute]

**Expected behavior:**
[What happens when you run it]

---

═══════════════════════════════════════════════════════════════════════════════
GUIDELINES
═══════════════════════════════════════════════════════════════════════════════

✓ Be specific and concrete (avoid vague statements)
✓ Use technical accuracy but explain in simple terms
✓ Focus on what the project DOES, not just what files exist
✓ Infer the purpose from the tech stack and structure
✓ If README is provided, use it as the source of truth
✓ If auto-analysis is provided, make educated inferences from:
  - Entry point file name and location
  - Imported frameworks (Flask = web app, argparse = CLI, etc)
  - Key module names (auth = authentication, db = database, etc)
  - File sizes (larger files = core logic)

✗ Don't say "I don't know" - make informed guesses based on evidence
✗ Don't just list files - explain their PURPOSE
✗ Don't use overly generic descriptions

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE OUTPUT
═══════════════════════════════════════════════════════════════════════════════

## 📋 Project Overview

**What it is:**
A chess game engine with AI opponent and graphical interface built in Python.

**Purpose:**
Provides an interactive chess experience where users can play against an AI that validates moves, detects check/checkmate, and renders the board visually.

---

## 🏗️ Architecture

**Type:** Desktop Game Application

**How it works:**
The application uses pygame for rendering the chess board and pieces. The game engine validates all moves according to chess rules, tracks game state, and allows players to make moves by clicking. An AI opponent uses minimax algorithm to calculate optimal moves.

**Entry Point:**
- File: `main.py`
- Function: `main()`

---

## ⚙️ Core Components

1. **Game Engine**
   - Purpose: Validates moves, detects check/checkmate, manages game state
   - Key files: `engine.py`, `validator.py`

2. **AI Opponent**
   - Purpose: Calculates best moves using minimax with alpha-beta pruning
   - Key files: `ai.py`, `evaluation.py`

3. **Graphics Renderer**
   - Purpose: Draws the board, pieces, and handles user clicks
   - Key files: `renderer.py`, `ui.py`

4. **Move System**
   - Purpose: Represents and executes chess moves with undo capability
   - Key files: `move.py`

---

## 🔧 Tech Stack

- **Language:** Python 3.x
- **Frameworks:** None - Pure Python
- **Key Libraries:** pygame (graphics), numpy (calculations)
- **Database:** Not applicable
- **Other:** Uses standard chess notation (PGN)

---

## 🚀 Getting Started

**To run this project:**
1. Install pygame: `pip install pygame`
2. Run: `python main.py`
3. Click on pieces to move them

**Expected behavior:**
A window opens showing a chess board. Click a piece to select it, then click a valid square to move. The AI will respond with its move.

---

═══════════════════════════════════════════════════════════════════════════════

Now analyze the provided project context and generate the explanation."""
    response = llm.invoke(prompt)
    print(response.content)
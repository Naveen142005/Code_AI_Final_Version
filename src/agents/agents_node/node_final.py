import re
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.agents_node.state import AgentState
from src.config import llm

def node_final(state: AgentState):

    query = state.get("resolved_query", "")
   
    research_list = state.get("research_results", []) or []
    diagram_list = state.get("diagram_results", []) or []
    
    retry_count = state.get("retry_count", 0)
    tool_history = state.get("tool_history", [])

    print(f"🎤 [Final node] => Synthesizing response... (Tools: {tool_history})")

   
   
    evidence_text = "\n\n".join(list(dict.fromkeys([str(r) for r in research_list])))
    
    valid_diagrams = []
    seen_diagrams = set()
    for d in diagram_list:
       
        if ("graph TD" in d or "classDef" in d) and d not in seen_diagrams:
            valid_diagrams.append(d)
            seen_diagrams.add(d)

    diagram_text = "\n\n".join(valid_diagrams)

   
   
    is_chat = "GeneralChat" in tool_history or (not evidence_text and not diagram_text)

    if is_chat:
        system_prompt = """You are a helpful Codebase Assistant.
        The user is engaging in conversation or asking a question where no code was found.
        Reply naturally, politely, and concisely. Do not invent code."""
    else:
        header_style = "Confident and Precise"
        if retry_count >= 3:
            header_style = "Cautious (Data Incomplete)"

        system_prompt = f"""
        ROLE: You are a Senior Principal Software Architect.
        TONE: {header_style}. Technical, Concisse, No Fluff.

        GOAL: Synthesize a technical answer using *only* the provided evidence.

        INPUT DATA:
        1. RESEARCH EVIDENCE: Raw file contents, symbol definitions, search results.
        2. DIAGRAM EVIDENCE: Mermaid.js graph code.

        ---------------------------------------------------
        🚫 NEGATIVE CONSTRAINTS (DO NOT DO THIS):
        - DO NOT say "Based on the evidence" or "I checked the files". Just state the facts.
        - DO NOT summarize code if you can show it. Show the actual function signatures.
        - DO NOT hallucinate code. If a file was not read, say "File content not available".
        - DO NOT apologize.
        ---------------------------------------------------

        ✅ POSITIVE INSTRUCTIONS:
        1. **Visuals**: If valid Mermaid code exists, render it first. Immediately below the diagram, write a 1-sentence caption explaining the flow.
        2. **Deep Dive**: When explaining logic, reference specific Line Numbers if available (e.g., "See `src/auth.py:45`").
        3. **Context**: Explain *why* the code works this way, don't just describe *what* it is.
        
        ---------------------------------------------------
        OUTPUT TEMPLATE (Follow Strictly):

        # [Direct Answer to Query]
        (Executive Summary - 2 sentences max)

        ## Architecture
        (Only if diagrams exist. Insert ```mermaid block here.)
        *(Brief caption explaining the data flow)*

        ## Implementation Details
        (Technical analysis. Use code blocks with filenames: `python file="src/utils.py"`)
        (Bulleted list of key logic flows)

        ## Referenced Sources
        - [File Path] (Function/Symbol accessed)
        ---------------------------------------------------
        """
            

    user_prompt = f"""
    QUERY: "{query}"

    --- RESEARCH EVIDENCE ---
    {evidence_text if evidence_text else "No text evidence."}

    --- DIAGRAM EVIDENCE ---
    {diagram_text if diagram_text else "No diagrams."}
    """

   
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        final_answer = response.content
    except Exception as e:
        print(f" [Final node] => Generation Error: {e}")
        final_answer = f"**Error Generating Report:** {e}\n\nHere is the raw data found:\n{evidence_text}"

    new_focus = state.get("context_focus")   
   
    hit = re.search(r"'file_path':\s*['\"]([^'\"]+\.py)['\"]", evidence_text)
    if hit:
        new_focus = hit.group(1)
        print(f"[Memory] Locked onto file: {new_focus}")
    
   
    elif not new_focus or new_focus == "None":
        hit_query = re.search(r'\b[\w/_\-]+\.py\b', query)
        if hit_query:
            new_focus = hit_query.group(0)
            print(f"[Memory] Inferred focus from query: {new_focus}")

    return {
        "final_response": final_answer,
        "context_focus": new_focus,
        "plan_step": "complete"
    }
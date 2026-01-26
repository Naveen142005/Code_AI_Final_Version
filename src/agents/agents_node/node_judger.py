import json
import re
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.agents_node.state import AgentState
from src.config import llm

def node_judge(state: AgentState):
    query = state.get("resolved_query", state.get("input", ""))
    research_results = state.get("research_results", [])
    diagram_results = state.get("diagram_results", [])
    retry_count = state.get("retry_count", 0)

    if retry_count >= 3:
        print(f"[Judger] => max retries ({retry_count}) reached. forcing'PASS'.")
        return {
            "plan_step": "critique_complete",
            "is_ok": True, 
            "critique_reason": "Max retries exceeded. Providing best effort answer."
        }

    evidence_text = "\n".join([str(r) for r in research_results])[:10000]
    visual_text = "\n".join([str(r) for r in diagram_results])[:2000]
    
    print('++++++++++++++++++++++++')
    print (evidence_text)
    print('++++++++++++++++++++++++')
    
    context_block = f"""
    --- TEXT EVIDENCE ---
    {evidence_text if evidence_text else "No text evidence found."}
    
    --- VISUAL EVIDENCE ---
    {visual_text if visual_text else "No diagrams generated."}
    """

    system_prompt = """You are the Quality Assurance Lead for a Codebase AI.
    Evaluate if the gathered evidence SUFFICIENTLY answers the user's query.

    CRITERIA FOR "PASS":
    1. The specific file/function/logic requested is present.
    2. If a diagram was asked for, 'VISUAL EVIDENCE' is not empty.
    3. Errors (FileNotFound) are handled or explained, not just dumped.

    CRITERIA FOR "FAIL":
    1. Evidence is purely "Error: File not found" or "I don't know".
    2. User asked for implementation (code), but only got a summary.
    3. User asked for a diagram, but 'VISUAL EVIDENCE' is empty.

    OUTPUT FORMAT:
    Return strictly valid JSON:
    {{
        "status": "PASS" | "FAIL",
        "reason": "Specific instruction for the Router on what to fix (e.g., 'File not found, try list_files_tool')."
    }}
    """

    user_prompt = f"QUERY: {query}\n\nEVIDENCE COLLECTED:\n{context_block}"

    status = "FAIL"
    reason = "Error in judgment logic"
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        cleaned = re.sub(r"```json|```", "", response.content).strip()
        verdict = json.loads(cleaned)
        
        print("=" * 60)
        print (verdict)
        print("=" * 60)
        status = verdict.get("status", "FAIL").upper()
        reason = verdict.get("reason", "Unknown failure")
        
    except Exception as e:
        print(f"[Judger] => Logic Error: {e}. Defaulting to FAIL.")
        reason = f"Judge crashed: {e}"

    print(f"[Judger] => status: {status} | Reason: {reason}")

    is_passing = (status == "PASS")

    if is_passing:
        return {
            "plan_step": "critique_complete",
            "is_ok": True,
            "critique_reason": "" 
        }
    else:
        return {
            "plan_step": "critique_complete", 
            "is_ok": False,
            "retry_count": retry_count + 1,
            "critique_reason": reason,
            
            "research_results": "RESET", 
            "diagram_results": "RESET" 
        }
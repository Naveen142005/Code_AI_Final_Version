
# --- CASE 1: The "None" Danger Zone ---
# Goal: LLM should NOT say "Refactor None" or "Refactor NO PRIOR CONTEXT"

def test_scenario(name, input_text, context):
    print(f"\n🧪 TEST: {name}")
    print(f"   Context: {context}")
    print(f"   Input:   '{input_text}'")
    
    # Run the Node
    result = node_listener({"input": input_text, "context_focus": context})
    output = result["resolved_query"]
    
    print(f"   Output:  '{output}'")
    return output


if __name__ == '__main__':
    print('hello')
    out1 = test_scenario("Fresh Start", "Refactor it", None)

    # --- CASE 2: The Happy Path ---
    # Goal: LLM SHOULD replace "it" with "auth.py"
    out2 = test_scenario("Memory Recall", "Refactor it", "auth.py")

    # --- CASE 3: The Topic Switch ---
    # Goal: LLM SHOULD ignore "auth.py" because user specified "main.py"
    out3 = test_scenario("Topic Switch", "Check main.py instead", "auth.py")

    # ==========================================
    # 4. VERDICT
    # ==========================================
    print("\n--- 🏁 FINAL VERDICT ---")

    if out1.lower() == "refactor it":
        print("✅ Case 1 (Fresh Start): PASSED (LLM didn't hallucinate context)")
    else:
        print(f"❌ Case 1 (Fresh Start): FAILED (LLM said: '{out1}')")

    if "auth.py" in out2:
        print("✅ Case 2 (Memory): PASSED (LLM resolved pronoun)")
    else:
        print(f"❌ Case 2 (Memory): FAILED (LLM said: '{out2}')")

    if "auth.py" not in out3 and "main.py" in out3:
        print("✅ Case 3 (Switch): PASSED (LLM respected new topic)")
    else:
        print(f"❌ Case 3 (Switch): FAILED (LLM got stuck on old context)")
        

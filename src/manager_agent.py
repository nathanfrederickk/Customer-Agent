import json
from llama_index.core import PromptTemplate, Settings

def manager_agent_node(state):
    """
    Node for the Manager Agent. Reviews the draft and makes a decision.
    
    Args:
        state (GraphState): The current state of the graph.

    Returns:
        dict: A dictionary with the final decision.
    """
    print("--- REVIEWING DRAFT ---")
    

    try:
        with open("./src/manager_prompt.md", "r") as f:
            MANAGER_AGENT_PROMPT = f.read()
            print("📝 System prompt loaded from manager_prompt.md.")
    except FileNotFoundError:
        print("❌ Error: manager_prompt.md not found in the root directory.")
        exit()

    prompt = PromptTemplate(MANAGER_AGENT_PROMPT).format(
        question=state["question"],
        context_str=state["context_str"],
        drafted_answer=state["drafted_answer"]
    )

    # Use the LLM to get the manager's decision
    response = Settings.llm.complete(prompt)
    
    try:
        # The manager is instructed to output JSON, so we parse it.
        decision_json = json.loads(str(response))
        print(f"Manager Decision: {decision_json}")
        return {"final_decision": decision_json}
    except json.JSONDecodeError:
        print("Manager failed to generate valid JSON. Defaulting to escalate.")
        return {"final_decision": {"decision": "escalate", "reason": "Invalid format from manager."}}

# <checklist_for_escalation>
# 1. Does the answer contain ANY uncertainty markers? ("usually", "might", "in most cases")
# 2. Is there risk of financial/legal harm if wrong?
# 3. Has user expressed frustration 2+ times?
# 4. Does the query involve edge cases not in our KB?
# 5. Would human verification add significant value?
# </checklist_for_escalation>

# <decision_rules>
# - If 3+ "yes" → Escalate to human
# - If 2 "yes" → Request clarification from user
# - Otherwise → Approve response
# </decision_rules>

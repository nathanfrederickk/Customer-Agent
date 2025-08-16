import json
from llama_index.core import PromptTemplate, Settings

def manager_agent_node(state):
    """
    Reviews the AI-drafted answer and decides on the next step.

    This node acts as a supervisor. It evaluates the initial question, the
    retrieved context, and the drafted answer to decide whether to approve
    the response, request revisions, or escalate to a human. It expects a
    structured JSON output from the LLM.

    Args:
        state (GraphState): The current state of the graph. This function reads
                            'question', 'context_str', and 'drafted_answer'.

    Returns:
        Dict[str, Any]: A dictionary containing the 'final_decision' from the manager.
    """
    print("--- REVIEWING DRAFT ---")

    # this prompt contains the instructions and criteria for the manager
    # to review the drafted answer.
    try:
        with open("./src/agents/manager_prompt.md", "r") as f:
            MANAGER_AGENT_PROMPT = f.read()
            print("📝 System prompt loaded from manager_prompt.md.")
    except FileNotFoundError:
        # agent cannot function without a prompt
        print("❌ Error: manager_prompt.md not found. Defaulting to escalate.")
        decision = {"decision": "escalate", "reason": "System Error: Manager prompt not found."}
        return {"final_decision": decision}

    # loading the prompt template and question
    prompt = PromptTemplate(MANAGER_AGENT_PROMPT).format(
        question=state["question"],
        context_str=state["context_str"],
        drafted_answer=state["drafted_answer"]
    )

    # the LLM acts as the manager, returning its decision in a JSON format.
    response = Settings.llm.complete(prompt)
    print(f"Manager raw response: {response}")

    # safely parse the LLM's JSON response.
    try:
        decision_json = json.loads(str(response))
        print(f"✅ Manager Decision: {decision_json}")
        return {"final_decision": decision_json}
    
    except json.JSONDecodeError as e:
        
        # if the manager LLM fails to return valid JSON, we cannot trust
        # the output, so we escalate as a fallback.
        print(f"❌ Manager failed to generate valid JSON: {e}. Defaulting to escalate.")
        decision = {"decision": "escalate", "reason": "Invalid format from manager model."}
        return {"final_decision": decision}

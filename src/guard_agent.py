# src/guardrail_agent.py

import json
from llama_index.core import PromptTemplate, Settings
from pydantic import BaseModel, Field

# --- Define the structured output for our guardrail ---
class GuardrailDecision(BaseModel):
    is_safe: bool = Field(description="True if the input is safe, otherwise False.")
    reason: str = Field(description="A brief explanation if the input is flagged as not safe.")


def guardrail_node(state):
    """
    Node for the input guardrail. Checks if the user's question is malicious.
    
    Args:
        state (GraphState): The current state of the graph.

    Returns:
        dict: A dictionary with the guardrail's decision.
    """
    print("--- RUNNING INPUT GUARDRAIL ---")
    question = state["question"]
    
     # Create the query engine with the specific drafting prompt
    try:
        with open("./src/guard_prompt.md", "r") as f:
            GUARDRAIL_PROMPT = f.read()
        print("📝 System prompt loaded from guard_prompt.md.")
    except FileNotFoundError:
        print("❌ Error: guard_prompt.md not found in the root directory.")
        exit()

    # Format the prompt for the guardrail
    prompt = PromptTemplate(GUARDRAIL_PROMPT).format(question=question)

    # Use the LLM to get the guardrail's decision
    # We ask the LLM to respond with a specific JSON structure for reliability
    response = Settings.llm.complete(prompt)
    print(response)
    
    try:
        decision_json = json.loads(str(response))
        decision = GuardrailDecision(**decision_json)
        print(f"Guardrail Decision: {decision.is_safe}, Reason: {decision.reason}")
        return {"guardrail_decision": decision}
    except (json.JSONDecodeError, TypeError):
        print("Guardrail failed to generate valid JSON. Defaulting to not safe.")
        return {"guardrail_decision": GuardrailDecision(is_safe=False, reason="Invalid format from guardrail.")}


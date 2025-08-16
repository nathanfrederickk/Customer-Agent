import json
from llama_index.core import PromptTemplate, Settings
from pydantic import BaseModel, Field

class GuardrailDecision(BaseModel):
    """
    A Pydantic model to structure the output from the guardrail LLM call.
    This ensures the response is predictable and easy to work with.

    Attributes:
        is_safe (bool): True if the input is deemed safe, False otherwise.
        reason (str): An explanation for the decision, especially if not safe.
    """
    is_safe: bool = Field(description="True if the input is safe, otherwise False.")
    reason: str = Field(description="A brief explanation if the input is flagged as not safe.")


def guardrail_node(state):
    """
    Acts as a security checkpoint to vet the user's question for malicious content.

    This node uses a language model with a specialized prompt to classify the
    input question. It expects a structured JSON response from the LLM to
    determine if the workflow can safely proceed.

    Args:
        state (GraphState): The current state of the graph. This function
                            reads the 'question' key.

    Returns:
        Dict[str, Any]: A dictionary containing the 'guardrail_decision', which is an
                        instance of the GuardrailDecision Pydantic model.
    """
    print("--- RUNNING INPUT GUARDRAIL ---")
    question = state["question"]
    
    # this prompt instructs the LLM on how to analyze the user's question
    # and what JSON structure to return.
    try:
        with open("./src/agents/guard_prompt.md", "r") as f:
            GUARDRAIL_PROMPT = f.read()
        print("📝 System prompt loaded from guard_prompt.md.")
    except FileNotFoundError:
        # guard rail cannot function without a prompt
        print("❌ Error: guard_prompt.md not found. Defaulting to not safe.")
        decision = GuardrailDecision(is_safe=False, reason="System Error: Guardrail prompt file not found.")
        return {"guardrail_decision": decision}

    # prompt template
    prompt = PromptTemplate(GUARDRAIL_PROMPT).format(question=question)

    # LLM evaluates the prompt and returns its decision in JSON format.
    response = Settings.llm.complete(prompt)
    print(f"Guardrail raw response: {response}")
    
    # safely parse the LLM's string response into the structured Pydantic model.
    try:
        decision_json = json.loads(str(response))
        decision = GuardrailDecision(**decision_json)
        print(f"✅ Guardrail Decision: Is Safe? {decision.is_safe}, Reason: {decision.reason}")
        return {"guardrail_decision": decision}
    
    except (json.JSONDecodeError, TypeError) as e:
        # if the LLM returns malformed JSON or unexpected data, default to flagging
        # the input as not safe to prevent potential security bypasses.
        print(f"❌ Guardrail failed to generate valid JSON: {e}. Defaulting to not safe.")
        decision = GuardrailDecision(is_safe=False, reason="Invalid format from guardrail model.")
        return {"guardrail_decision": decision}

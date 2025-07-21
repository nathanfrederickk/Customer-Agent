# src/agents/customer_agent.py

from llama_index.core import PromptTemplate

def customer_agent_node(state, index):
    """
    Node for the Customer Agent. Retrieves context and drafts an answer.
    
    Args:
        state (GraphState): The current state of the graph.
        index (VectorStoreIndex): The LlamaIndex object to query.

    Returns:
        dict: A dictionary with the context and the drafted answer.
    """
    print("--- DRAFTING ANSWER ---")
    question = state["question"]

    # Load the prompt from the external file
    try:
        with open("./src/agents/customer_prompt.md", "r") as f:
            CUSTOMER_AGENT_PROMPT = f.read()
        print("📝 System prompt loaded from customer_prompt.md.")
    except FileNotFoundError:
        print("❌ Error: customer_prompt.md not found in the 'src/agents' directory.")
        # Return a failure state for the manager to see
        return {
            "context_str": "System Error: Prompt file not found.",
            "drafted_answer": "I was unable to find a definitive answer due to a system error."
        }

    qa_template = PromptTemplate(CUSTOMER_AGENT_PROMPT)

    # Instead of retrieving manually, we configure the query engine to do it.
    # This allows LlamaIndex to use more advanced strategies.
    query_engine = index.as_query_engine(
        # text_qa_template=qa_template,
    )
    
    # Generate the draft answer. The engine now handles both retrieval and synthesis.
    response_object = query_engine.query(question)
    
    # Extract the drafted answer and the context that was actually used
    drafted_answer = str(response_object)
    print(response_object)
    context_str = "\n\n".join([node.get_content() for node in response_object.source_nodes])

    # --- A great debugging tip for the future ---
    # print("\n--- RETRIEVED CONTEXT ---")
    # print(context_str)
    # print("-------------------------\n")

    return {
        "context_str": context_str,
        "drafted_answer": drafted_answer
    }

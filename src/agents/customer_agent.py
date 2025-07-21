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

    # Use a retriever to find relevant context
    retriever = index.as_retriever(similarity_top_k=4)
    retrieved_nodes = retriever.retrieve(question)
    context_str = "\n\n".join([n.get_content() for n in retrieved_nodes])

    # Create the query engine with the specific drafting prompt
    try:
        with open("./src/agents/customer_prompt.md", "r") as f:
            CUSTOMER_AGENT_PROMPT = f.read()
        print("📝 System prompt loaded from customer_prompt.md.")
    except FileNotFoundError:
        print("❌ Error: customer_prompt.md not found in the root directory.")
        exit()

    qa_template = PromptTemplate(CUSTOMER_AGENT_PROMPT)

    query_engine = index.as_query_engine(
        text_qa_template=qa_template,
    )
    
    # Generate the draft answer
    drafted_answer = query_engine.query(question)
    print(drafted_answer)
    return {
        "context_str": context_str,
        "drafted_answer": str(drafted_answer)
    }

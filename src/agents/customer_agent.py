from llama_index.core import Settings
from llama_index.core.prompts import PromptTemplate
from llama_index.core.retrievers import VectorIndexRetriever

def extract_first_name(sender: str) -> str:
    """
    Extracts the first name from an email sender string.

    This utility function parses strings like "John Doe <john.doe@example.com>"
    or "jane.doe@example.com" to produce a friendly first name for personalization.

    Args:
        sender (str): The sender string from the email's 'From' header.

    Returns:
        str: The extracted first name. Returns a default name ("User") if
             no name can be clearly identified.
    """
    default_name = "User"
    # handles formats like: "John Doe" <j.doe@example.com>
    if '<' in sender:
        # isolate the name part before the '<'
        name_part = sender.split('<')[0].strip().replace('"', '')
        # return the first word of the name part, or default if empty
        return name_part.split()[0] if name_part else default_name
    else:
        # handles formats like: jane.doe@example.com
        # takes the part before the '@' and then before the first '.'
        return sender.split('@')[0].split('.')[0]

def customer_agent_node(state, index):
    """
    Drafts a customer service response using a retrieval-augmented generation (RAG) pipeline.

    This node performs the core logic of the AI agent. It takes the user's question,
    retrieves relevant context from a knowledge base (VectorStoreIndex), formats this
    information into a detailed prompt, and then calls a language model to generate
    a draft answer.

    Args:
        state (GraphState): The current state of the graph. This function reads the
                            'question' and 'original_email' keys.
        index (VectorStoreIndex): The LlamaIndex vector store containing the
                                  knowledge base for retrieval.

    Returns:
        Dict[str, Any]: A dictionary with the 'context_str' and 'drafted_answer'
                        to be merged back into the graph's state.
    """
    print("--- DRAFTING ANSWER ---")
    question = state["question"]
    sender = state["original_email"]["sender"]

    # extract the user's first name for a more personal response.
    first_name = extract_first_name(sender)
    print(f"📝 Parsed user's first name: {first_name}")

    # the system prompt provides the core instructions for the LLM.
    try:
        with open("./src/agents/customer_prompt.md", "r") as f:
            template_str = f.read()
        print("📝 System prompt loaded from customer_prompt.md.")
    except FileNotFoundError:
        # handle cases where the prompt file is missing to prevent a crash.
        return {
            "context_str": "System Error: Prompt file not found.",
            "drafted_answer": "I was unable to find a definitive answer due to a system error."
        }

    # fetch relevant documents from the knowledge base (vector index).
    qa_template = PromptTemplate(template_str)
    retriever = VectorIndexRetriever(index=index, similarity_top_k=2)
    retrieved_nodes = retriever.retrieve(question)
    context_str = "\n\n".join([node.get_content() for node in retrieved_nodes])

    # manually format the prompt with all the necessary variables (context,
    # question, and personalized name). This gives us full control over the
    # final input to the LLM.
    final_prompt = qa_template.format(
        context_str=context_str,
        query_str=question,
        user_first_name=first_name
    )
    
    # call the LLM directly with the fully constructed prompt to get the answer.
    response = Settings.llm.complete(final_prompt)
    drafted_answer = str(response)
    print(f"✅ Drafted Answer:\n{drafted_answer}")

    # Return the new information to be added to the graph's state.
    return {
        "context_str": context_str,
        "drafted_answer": drafted_answer
    }
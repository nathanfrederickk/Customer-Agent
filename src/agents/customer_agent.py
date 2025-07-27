from llama_index.core import Settings
from llama_index.core.prompts import PromptTemplate
from llama_index.core.retrievers import VectorIndexRetriever

def extract_first_name(sender: str) -> str:
    """Extracts first name from email sender string"""
    default_name = "User"
    if '<' in sender:
        name_part = sender.split('<')[0].strip().replace('"', '')
        return name_part.split()[0] if name_part else default_name
    else:
        return sender.split('@')[0].split('.')[0]

def customer_agent_node(state, index):
    """
    Node for the Customer Agent. Uses an explicit retrieve -> format -> complete
    pipeline to correctly handle custom variables.
    """
    print("--- DRAFTING ANSWER ---")
    question = state["question"]
    sender = state["original_email"]["sender"]
    first_name = extract_first_name(sender)
    print(f"📝 Parsed user's first name: {first_name}")

    # Load the prompt template string from the file
    try:
        with open("./src/agents/customer_prompt.md", "r") as f:
            template_str = f.read()
        print("📝 System prompt loaded from customer_prompt.md.")
    except FileNotFoundError:
        return {
            "context_str": "System Error: Prompt file not found.",
            "drafted_answer": "I was unable to find a definitive answer due to a system error."
        }

    # 1. Create the PromptTemplate instance
    qa_template = PromptTemplate(template_str)
    
    # 2. Explicitly retrieve the context
    retriever = VectorIndexRetriever(index=index, similarity_top_k=2)
    retrieved_nodes = retriever.retrieve(question)
    context_str = "\n\n".join([node.get_content() for node in retrieved_nodes])

    # 3. Manually format the prompt with all variables
    final_prompt = qa_template.format(
        context_str=context_str,
        query_str=question,
        user_first_name=first_name
    )
    
    # 4. Call the LLM directly with the fully formatted prompt
    response = Settings.llm.complete(final_prompt)
    drafted_answer = str(response)
    print(drafted_answer)

    return {
        "context_str": context_str,
        "drafted_answer": drafted_answer
    }

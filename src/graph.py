import os
import chromadb
from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph, END
from functools import partial

# import agents
from src.agents.guard_agent import guardrail_node, GuardrailDecision
from src.agents.customer_agent import customer_agent_node
from src.agents.manager_agent import manager_agent_node
from src.email_sender_node import email_sender_node 

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from utils.secret_manager import get_secret

# fetching the key from AWS Secrets Manager
gemini_api_key = get_secret("prod/CustomerAgent/GeminiApiKeyS")

# setting the environment variable so LlamaIndex can find it
if gemini_api_key:
    os.environ['GOOGLE_API_KEY'] = gemini_api_key
    print("✅ API Key fetched from AWS and loaded into environment.")

# no Gemini API key is found  
else:
    print("❌ Failed to fetch Gemini API Key from AWS.")
    exit()

# setting the Gemini model
Settings.llm = Gemini(model="models/gemini-2.5-flash")
Settings.embed_model = GeminiEmbedding(model_name="models/embedding-001")
print("⚙️ LlamaIndex components configured.")

# ChromDB setup in the temp folder (used in serverless Lambda)
db = chromadb.PersistentClient(path= "/tmp/chroma_db")
chroma_collection = db.get_or_create_collection("visa_agent_collection")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# initialize the document if no vector database is found
if chroma_collection.count() == 0:
    print("📄 Collection is empty. Ingesting new documents.")
    try:
        reader = SimpleDirectoryReader(input_files=["./data/485Visa.md"])
        documents = reader.load_data()
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        print("✅ Index created and stored successfully.")
    except Exception as e:
        print(f"❌ Error during initial document ingestion: {e}")
        exit()
else: # if the chromaDB already exist
    print("✅ Loading index from existing ChromaDB collection.")
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    print("✅ Index loaded successfully.")

# define the graph state (LangGraph)
class GraphState(TypedDict):
    question: str
    original_email: dict 
    context_str: str
    chat_history: str
    drafted_answer: str
    guardrail_decision: GuardrailDecision
    final_decision: dict

def escalation_node(state: GraphState):
    """
    Handles the terminal state of escalating a task to a human.

    This node logs the reason for escalation by checking the state for decisions
    made by the guardrail or the manager. It serves as a final step for any
    branch of the graph that requires human intervention.

    Args:
        state (GraphState): The current state of the graph.

    Returns:
        An empty dictionary, as it does not modify the state.
    """
    print("--- ESCALATING TO HUMAN ---")

    guard_decision = state.get("guardrail_decision")
    manager_decision = state.get("final_decision")
    reason = "No reason provided."

    # determine the reason based on which node triggered the escalation.
    if guard_decision and not guard_decision.is_safe:
        reason = guard_decision.reason
    elif manager_decision:
        reason = manager_decision.get("reason", "Manager escalated.")
    
    print(f"Reason for Escalation: {reason}")
    return {}

def should_process(state: GraphState) -> str:
    """
    A conditional edge that routes the workflow after the guardrail check.

    This function inspects the 'guardrail_decision' in the state to decide
    the next step.

    Args:
        state (GraphState): The current state of the graph.

    Returns:
        'continue': If the input is deemed safe by the guardrail.
        'escalate': If the input is flagged as not safe.
    """
    print("--- ROUTING AFTER GUARDRAIL ---")

    if state["guardrail_decision"].is_safe:
        print("Decision: Continue to customer agent.")
        return "continue"
    else:
        print("Decision: Escalate to human.")
        return "escalate"

def should_escalate(state: GraphState) -> str:
    """
    A conditional edge that routes the workflow after the manager's review.

    This function inspects the 'final_decision' from the manager to determine
    whether to send the email or escalate to a human.

    Args:
        state (GraphState): The current state of the graph.

    Returns:
        'send_email': If the manager's decision is 'send'.
        'escalate': For any other decision from the manager.
    """
    print("--- ROUTING AFTER MANAGER ---")

    if state["final_decision"].get("decision") == "send":
        print("Decision: Approved. Proceed to send email.")
        return "send_email"
    else:
        print("Decision: Manager did not approve. Escalating.")
        return "escalate"

def build_graph(gmail_service, index):
    """
    Constructs and compiles the LangGraph StateGraph for the customer service agent.

    This function wires together all the nodes (processing steps) and edges
    (logic for moving between steps) to create the complete, runnable workflow.

    Args:
        gmail_service: An authenticated Google API client for sending emails.
        index: The LlamaIndex VectorStoreIndex for the RAG agent.

    Returns:
        A compiled LangGraph workflow ready to be executed.
    """
    workflow = StateGraph(GraphState)

    # use functools.partial to pre-fill arguments for nodes that need external dependencies.
    customer_agent_with_index = partial(customer_agent_node, index=index)
    email_sender_with_service = partial(email_sender_node, service=gmail_service) 

    # add all the defined functions as nodes in the graph.
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("customer_agent", customer_agent_with_index)
    workflow.add_node("manager_agent", manager_agent_node)
    workflow.add_node("send_email", email_sender_with_service) 
    workflow.add_node("escalate", escalation_node)

    # defining the graph path
    # The entry point is the guardrail.
    workflow.set_entry_point("guardrail")

    # after the guardrail, decide whether to continue or escalate.
    workflow.add_conditional_edges(
        "guardrail",
        should_process,
        {"continue": "customer_agent", "escalate": "escalate"},
    )

    # after the customer agent drafts a response, it always goes to the manager.
    workflow.add_edge("customer_agent", "manager_agent")

    # after the manager reviews, decide whether to send the email or escalate.
    workflow.add_conditional_edges(
        "manager_agent",
        should_escalate,
        {"send_email": "send_email", "escalate": "escalate"},
    )

    # define the end points of the graph.
    workflow.add_edge("send_email", END)
    workflow.add_edge("escalate", END)

    # compile the graph into a runnable object.
    return workflow.compile()

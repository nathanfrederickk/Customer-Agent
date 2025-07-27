# src/graph.py

import os
import chromadb
from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph, END
from functools import partial

# --- Import Agent Nodes ---
from agents.guard_agent import guardrail_node, GuardrailDecision
from agents.customer_agent import customer_agent_node
from agents.manager_agent import manager_agent_node
from email_sender_node import email_sender_node 

# --- Import LlamaIndex Components ---
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# --- 1. Initial Setup ---
load_dotenv()
print("✅ API Key loaded.")

Settings.llm = Gemini(model="models/gemini-2.5-flash")
Settings.embed_model = GeminiEmbedding(model_name="models/embedding-001")
print("⚙️  LlamaIndex components configured.")

# --- 2. Setup Persistent ChromaDB and Load/Create Index ---
db = chromadb.PersistentClient(path="../chroma_db")
chroma_collection = db.get_or_create_collection("visa_agent_collection")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

if chroma_collection.count() == 0:
    print("📄 Collection is empty. Ingesting new documents...")
    try:
        reader = SimpleDirectoryReader(input_files=["./data/485Visa.md"])
        documents = reader.load_data()
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        print("✅ Index created and stored successfully.")
    except Exception as e:
        print(f"❌ Error during initial document ingestion: {e}")
        exit()
else:
    print("✅ Loading index from existing ChromaDB collection.")
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    print("✅ Index loaded successfully.")

# --- 3. Define the Graph State ---
class GraphState(TypedDict):
    question: str
    original_email: dict 
    context_str: str
    chat_history: str
    drafted_answer: str
    guardrail_decision: GuardrailDecision
    final_decision: dict

# --- 4. Define Supporting Nodes and Edges ---
def escalation_node(state: GraphState):
    print("--- ESCALATING TO HUMAN ---")
    guard_decision = state.get("guardrail_decision")
    manager_decision = state.get("final_decision")
    reason = "No reason provided."
    if guard_decision and not guard_decision.is_safe:
        reason = guard_decision.reason
    elif manager_decision:
        reason = manager_decision.get("reason", "Manager escalated.")
    print(f"Reason: {reason}")
    return {}

def should_process(state: GraphState):
    print("--- ROUTING AFTER GUARDRAIL ---")
    return "continue" if state["guardrail_decision"].is_safe else "escalate"

def should_escalate(state: GraphState):
    print("--- ROUTING AFTER MANAGER ---")
    # If the manager approves, go to the new send_email node
    return "send_email" if state["final_decision"].get("decision") == "send" else "escalate"

# --- 5. Build the Graph ---
def build_graph(gmail_service):
    workflow = StateGraph(GraphState)

    customer_agent_with_index = partial(customer_agent_node, index=index)
    email_sender_with_service = partial(email_sender_node, service=gmail_service) 

    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("customer_agent", customer_agent_with_index)
    workflow.add_node("manager_agent", manager_agent_node)
    workflow.add_node("send_email", email_sender_with_service) 
    workflow.add_node("escalate", escalation_node)

    workflow.set_entry_point("guardrail")
    workflow.add_conditional_edges(
        "guardrail",
        should_process,
        {"continue": "customer_agent", "escalate": "escalate"},
    )
    workflow.add_edge("customer_agent", "manager_agent")
    workflow.add_conditional_edges(
        "manager_agent",
        should_escalate,
        {"send_email": "send_email", "escalate": "escalate"},
    )
    workflow.add_edge("send_email", END)
    workflow.add_edge("escalate", END)

    return workflow.compile()


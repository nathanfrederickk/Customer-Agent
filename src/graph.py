import os
import chromadb
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from functools import partial

# --- Import Agent Nodes ---
from customer_agent import customer_agent_node
from manager_agent import manager_agent_node

# --- Import LlamaIndex Components ---
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# --- 1. Initial Setup ---
load_dotenv()
print("✅ API Key loaded.")

# Configure LlamaIndex Settings
Settings.llm = Gemini(model="models/gemini-2.5-flash")
Settings.embed_model = GeminiEmbedding(model_name="models/embedding-001")
print("⚙️  LlamaIndex components configured.")

# Connect to the existing vector store
db = chromadb.PersistentClient(path="../chroma_db")
chroma_collection = db.get_or_create_collection("visa_agent_collection")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
print("✅ Index loaded from ChromaDB.")

# --- 2. Define the Graph State ---
class GraphState(TypedDict):
    question: str
    context_str: str
    chat_history: str
    drafted_answer: str
    final_decision: dict

# --- 3. Define Supporting Nodes and Edges ---

def escalation_node(state: GraphState):
    print("--- ESCALATING TO HUMAN ---")
    print("Reason:", state["final_decision"].get("reason", "No reason provided."))
    return {}

def should_escalate(state: GraphState):
    print("--- ROUTING DECISION ---")
    decision = state["final_decision"].get("decision", "escalate")
    return "escalate" if decision == "escalate" else "end"

# --- 4. Build the Graph ---

workflow = StateGraph(GraphState)

# Use partial to pass the 'index' object to the customer agent node
customer_agent_with_index = partial(customer_agent_node, index=index)

# Add the nodes to the graph
workflow.add_node("customer_agent", customer_agent_with_index)
workflow.add_node("manager_agent", manager_agent_node)
workflow.add_node("escalate", escalation_node)

# Define the workflow connections
workflow.set_entry_point("customer_agent")
workflow.add_edge("customer_agent", "manager_agent")
workflow.add_conditional_edges(
    "manager_agent",
    should_escalate,
    {"escalate": "escalate", "end": END},
)
workflow.add_edge("escalate", END)

# Compile the graph
app = workflow.compile()
print("\n🚀 LangGraph workflow compiled!")

# --- 5. Run the Application ---

if __name__ == "__main__":
    inputs = {
        "question": "can you tell me about the 500 subclass visa?",
        "chat_history": ""
    }
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"Output from node '{key}':")
            # print(value) # Uncomment to see the full state

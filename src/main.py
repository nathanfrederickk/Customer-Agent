# src/main.py

import os
import chromadb
from dotenv import load_dotenv

# --- 1. Load Environment Variables ---
load_dotenv()
print("✅ API Key loaded from .env file.")

# --- 2. Setup LlamaIndex Components ---
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

Settings.llm = Gemini(model="models/gemini-2.5-flash")
Settings.embed_model = GeminiEmbedding(model_name="models/embedding-001")

print("⚙️  LlamaIndex components configured.")

# --- 3. Setup Persistent ChromaDB Vector Store ---
# This step now happens before loading/creating the index.
# We create a persistent client that saves the DB to a folder named 'chroma_db'.
db = chromadb.PersistentClient(path="../chroma_db")
chroma_collection = db.get_or_create_collection("visa_agent_collection")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

print("🧠 ChromaDB vector store is ready.")

# --- 4. Load or Create the Index (The Efficient Way) ---
# We check if the ChromaDB collection is empty.
# If it's empty, we ingest the document. Otherwise, we load the existing index.

if chroma_collection.count() == 0:
    print("📄 Collection is empty. Ingesting new documents... (This happens only once)")
    try:
        # Load documents from file
        # Note: The path is relative to the 'src' folder where this script runs.
        reader = SimpleDirectoryReader(input_files=["../data/485Visa.md"])
        documents = reader.load_data()
        print(f"📄 Loaded {len(documents)} document(s).")
        
        # Create index from documents. This automatically populates the ChromaDB collection.
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context
        )
        print("✅ Index created and stored successfully.")
    except Exception as e: 
        print(f"❌ Error during initial document ingestion: {e}")
        exit()
else:
    print("✅ Loading index from existing ChromaDB collection.")
    # If the collection is not empty, we don't need to read the file again.
    # We can load the index directly from our vector store.
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
    )
    print("✅ Index loaded successfully.")


# --- 5. Create the Query Engine ---
# This part remains the same.
query_engine = index.as_query_engine(streaming=True)
print("\n🚀 Query engine is ready! Ask a question about the Temporary Graduate visa.")
print("   Type 'exit' to quit.\n")


# --- 6. Start Interactive Query Loop ---
# This part remains the same.
while True:
    prompt = input("Your question: ")
    if prompt.lower() == 'exit':
        print("Exiting. Goodbye!")
        break

    # Query the engine and stream the response
    response = query_engine.query(prompt)
    
    print("\nAgent's answer:")
    response.print_response_stream()
    print("\n" + "="*50 + "\n")


import os
import chromadb

from dotenv import load_dotenv

# --- 1. Load Environment Variables ---
# This line loads the GOOGLE_API_KEY from your .env file.
load_dotenv()
print("✅ API Key loaded from .env file.")

# --- 2. Setup LlamaIndex Components ---
# We configure the necessary components from LlamaIndex.
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding  

# Set up the core components. We use Google's Gemini model for generation
# and another Google model for creating embeddings (numerical representations of text).
# Replace PaLM embeddings with Gemini embeddings
Settings.llm = Gemini(model="models/gemini-2.5-flash")
Settings.embed_model = GeminiEmbedding(model_name="models/embedding-001")  # Updated

print("⚙️  LlamaIndex components configured.")

# --- 3. Load Documents ---
# This reads all the files from the specified directory.
# We point it to the 'data' folder in the parent directory.
# Note the '../data' path, which means "go up one level from 'src', then into 'data'".
try:
    reader = SimpleDirectoryReader(input_files=["./data/485Visa.md"])
    documents = reader.load_data()
    print(f"📄 Loaded {len(documents)} document(s).")
except Exception as e:
    print(f"❌ Error loading documents: {e}")
    print("Please make sure you have a 'data/source_documents' folder in your project root with your .md file inside.")
    exit()


# --- 4. Setup ChromaDB Vector Store ---
# This is where our embeddings will be stored.
# We create a persistent client to save the database to disk.
db = chromadb.PersistentClient(path="../chroma_db")
chroma_collection = db.get_or_create_collection("visa_agent_collection")

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

print("🧠 ChromaDB vector store is ready.")

# --- 5. Create and Store the Index ---
# This is the main step. LlamaIndex will:
# 1. Break the documents into chunks (nodes).
# 2. Convert each chunk into a vector embedding using the embedding model.
# 3. Store these embeddings in our ChromaDB collection.
# If the index is already stored, it will be loaded instead of re-created.
index = VectorStoreIndex.from_documents(
    documents, storage_context=storage_context
)
print("✅ Index created and stored successfully.")


# --- 6. Create the Query Engine ---
# This engine is what we'll use to ask questions.
# It takes a question, finds relevant chunks from the index,
# and passes them to the LLM to generate an answer.
query_engine = index.as_query_engine(streaming=True)
print("\n🚀 Query engine is ready! Ask a question about the Temporary Graduate visa.")
print("   Type 'exit' to quit.\n")


# --- 7. Start Interactive Query Loop ---
while True:
    prompt = input("Your question: ")
    if prompt.lower() == 'exit':
        print("Exiting. Goodbye!")
        break

    # Query the engine and stream the response
    response = query_engine.query(prompt)
    
    print("\nAgent's answer:")
    # The 'response.print_response_stream()' method will print the
    # answer token by token as it's generated.
    response.print_response_stream()
    print("\n" + "="*50 + "\n")
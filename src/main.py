# main_llamaindex.py

# --- 1. Installation ---
# Before running, install the necessary LlamaIndex libraries:

import os
import chromadb
from getpass import getpass

# --- 2. API Key Setup ---
if "GOOGLE_API_KEY" not in os.environ:
    print("🔑 Google API Key not found. Please enter it below.")
    os.environ["GOOGLE_API_KEY"] = getpass("Enter your Google API Key: ")
    print("✅ API Key set for this session.")
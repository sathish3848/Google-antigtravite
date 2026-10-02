"""
Configuration module for the Annual Report Q&A Assistant.
Handles environment variables, SSL certificate store injection for Windows,
model definitions, chunking parameters, and prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Automatically inject Windows/system certificate store into SSL
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# Load environment variables from .env
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Model configuration
# Target model requested: gemini-3.8-flash
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Fallback & alternative models supported by Google GenAI
AVAILABLE_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemma-4-26b-a4b-it",
    "gemini-flash-latest",
]

# Embedding model
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

# Chunking configuration (Step 2 in workflow: chunk_size=1000, overlap=150)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Retrieval configuration (Step 5 in workflow: k=4)
TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", "4"))

# Key financial prompt from Project Specification Section 4
FINANCIAL_QA_PROMPT = """You are a financial analyst assistant.
Answer the question using ONLY the context below.
If the answer is not in the context, say "I could not find this in the report."
Mention the page number for every fact you use.

Context: {context}
Question: {question}
"""

"""
Ingestion Pipeline for Annual Report Q&A Assistant.
Implements Steps 1 to 4 of the workflow:
Step 1: Load PDF using PyPDFLoader (metadata includes page numbers)
Step 2: Chunk text using RecursiveCharacterTextSplitter (chunk size 1000, overlap 150)
Step 3: Create embeddings using Gemini embeddings (models/gemini-embedding-001)
Step 4: Store vectors in ChromaDB (persisted to local directory chroma_db/)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import config

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


def get_embedding_function(model_name: Optional[str] = None):
    """
    Initializes and returns the embedding function for ChromaDB.
    Defaults to Gemini embeddings (gemini-embedding-001).
    """
    model = model_name or config.DEFAULT_EMBEDDING_MODEL
    api_key = config.GOOGLE_API_KEY
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Please add it to your .env file or environment variables."
        )
    return GoogleGenerativeAIEmbeddings(
        model=model,
        google_api_key=api_key,
    )


def get_vectorstore(
    persist_directory: Optional[Path] = None,
    collection_name: str = "annual_reports",
    embedding_function=None,
) -> Chroma:
    """
    Returns an instance of ChromaDB connected to the persistent store.
    """
    persist_dir = persist_directory or config.CHROMA_DIR
    embeddings = embedding_function or get_embedding_function()

    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )


def load_pdf(pdf_path: str | Path) -> List[Document]:
    """
    Step 1: Load PDF using PyPDFLoader.
    Extracts text per page and normalizes page numbers to 1-indexed for standard human readability.
    """
    path_obj = Path(pdf_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"PDF file not found at: {path_obj}")

    loader = PyPDFLoader(str(path_obj))
    pages = loader.load()

    # Normalize metadata: ensure page is 1-indexed and clean source filename
    for doc in pages:
        raw_page = doc.metadata.get("page", 0)
        # PyPDFLoader pages are 0-indexed, convert to 1-indexed for user citations
        doc.metadata["page"] = int(raw_page) + 1
        doc.metadata["source"] = path_obj.name
        doc.metadata["file_path"] = str(path_obj.resolve())

    return pages


def chunk_documents(
    documents: List[Document],
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> List[Document]:
    """
    Step 2: Chunk text using RecursiveCharacterTextSplitter.
    Default parameters: chunk size 1000, overlap 150.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    return chunks


def ingest_pdf(
    pdf_path: str | Path,
    vectorstore: Optional[Chroma] = None,
    clear_existing_source: bool = False,
) -> Dict[str, Any]:
    """
    Full Indexing Pipeline (Steps 1 to 4):
    1. Load PDF
    2. Chunk text
    3. Embed chunks
    4. Store into ChromaDB
    """
    path_obj = Path(pdf_path)
    filename = path_obj.name

    print(f"\n[1/4] Loading PDF: {filename}...")
    pages = load_pdf(path_obj)
    total_pages = len(pages)
    print(f"      Loaded {total_pages} page(s).")

    print(f"[2/4] Chunking document (chunk_size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP})...")
    chunks = chunk_documents(pages)
    total_chunks = len(chunks)
    print(f"      Generated {total_chunks} chunk(s).")

    print(f"[3/4 & 4/4] Creating embeddings and storing into ChromaDB...")
    db = vectorstore or get_vectorstore()

    # If requested or replacing, clear existing chunks for this specific document source
    if clear_existing_source:
        try:
            # Query existing IDs for this source and delete
            existing_results = db.get(where={"source": filename})
            if existing_results and existing_results.get("ids"):
                db.delete(ids=existing_results["ids"])
                print(f"      Removed {len(existing_results['ids'])} previous chunks for {filename}.")
        except Exception as e:
            print(f"      Note: Could not clear existing source records: {e}")

    # Add chunks with metadata
    db.add_documents(chunks)
    print(f"      Successfully persisted {total_chunks} chunks to {config.CHROMA_DIR}!")

    return {
        "filename": filename,
        "total_pages": total_pages,
        "total_chunks": total_chunks,
        "status": "success",
    }


def ingest_all_pdfs(data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Scans the data directory and ingests all PDF files found.
    """
    target_dir = data_dir or config.DATA_DIR
    pdf_files = list(target_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in directory: {target_dir}")
        return []

    print(f"Found {len(pdf_files)} PDF file(s) in {target_dir} to ingest.")
    results = []
    db = get_vectorstore()

    for pdf in pdf_files:
        res = ingest_pdf(pdf, vectorstore=db, clear_existing_source=True)
        results.append(res)

    return results


def get_indexed_sources(vectorstore: Optional[Chroma] = None) -> List[str]:
    """
    Returns a sorted list of unique PDF sources currently indexed in ChromaDB.
    """
    db = vectorstore or get_vectorstore()
    try:
        data = db.get()
        metadatas = data.get("metadatas", [])
        sources = {m.get("source") for m in metadatas if m and m.get("source")}
        return sorted(list(sources))
    except Exception:
        return []


if __name__ == "__main__":
    # If a specific PDF argument is passed via CLI, ingest that.
    # Otherwise ingest all PDFs in data/
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
        ingest_pdf(target_path, clear_existing_source=True)
    else:
        ingest_all_pdfs()

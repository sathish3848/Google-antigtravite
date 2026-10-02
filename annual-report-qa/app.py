"""
Streamlit Web Application for Annual Report Q&A Assistant.
Provides a modern financial chat interface with:
- PDF upload & automatic ingestion into ChromaDB
- Source citations with exact page numbers
- Multi-document switcher
- Model selector (gemini-3.8-flash default)
- Chat memory & conversation history
- Context inspection accordion
"""

import os
import sys
import time
from pathlib import Path
import streamlit as st

import config
from ingest import (
    ingest_pdf,
    get_vectorstore,
    get_indexed_sources,
)
from rag_chain import FinancialRAGChain

# Page configuration
st.set_page_config(
    page_title="Annual Report Q&A Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Financial Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .citation-badge {
        display: inline-block;
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.8rem;
        margin-right: 0.4rem;
        margin-top: 0.4rem;
        border: 1px solid #BFDBFE;
    }
    .model-badge {
        display: inline-block;
        background-color: #F1F5F9;
        color: #475569;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        margin-left: 0.5rem;
        font-family: monospace;
    }
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "quick_question" not in st.session_state:
    st.session_state.quick_question = None


@st.cache_resource
def load_db():
    return get_vectorstore()


db = load_db()

# ================= SIDEBAR =================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bullish.png", width=64)
    st.title("Financial RAG Settings")
    st.caption("Powered by Gemini & ChromaDB")

    st.markdown("---")
    st.subheader("📁 1. Annual Report Upload")
    uploaded_file = st.file_uploader(
        "Upload Annual Report (PDF)",
        type=["pdf"],
        help="Upload a company's Annual Report or 10-K to index and query.",
    )

    if uploaded_file is not None:
        target_path = config.DATA_DIR / uploaded_file.name
        if not target_path.exists():
            with open(target_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Saved: {uploaded_file.name}")

            with st.spinner("Extracting pages, generating chunks & embedding into ChromaDB..."):
                t0 = time.time()
                res = ingest_pdf(target_path, vectorstore=db, clear_existing_source=True)
                dur = round(time.time() - t0, 1)
                st.success(f"Indexed {res['total_pages']} pages ({res['total_chunks']} chunks) in {dur}s!")
                st.rerun()

    # Document Selection (Feature: Multiple PDF Support)
    indexed_sources = get_indexed_sources(db)
    st.subheader("📑 2. Active Report")
    if indexed_sources:
        doc_options = ["All Indexed Reports"] + indexed_sources
        selected_doc = st.selectbox(
            "Select Target Report",
            options=doc_options,
            index=0,
            help="Filter your questions to a specific annual report or search across all.",
        )
        active_filter = None if selected_doc == "All Indexed Reports" else selected_doc
    else:
        st.warning("No documents indexed yet. Please upload a PDF or run ingest.")
        active_filter = None

    st.markdown("---")
    st.subheader("⚙️ 3. LLM & Retrieval")

    selected_model = st.selectbox(
        "Gemini Model",
        options=config.AVAILABLE_MODELS,
        index=0,  # Default to gemini-3.8-flash
        help="Target model: gemini-3.8-flash with fallback resilience.",
    )

    top_k = st.slider(
        "Top-K Retrieved Chunks",
        min_value=2,
        max_value=8,
        value=config.TOP_K_CHUNKS,
        step=1,
        help="Number of most relevant text chunks to provide as context (Default: 4).",
    )

    st.markdown("---")
    st.subheader("📊 Index Status")
    st.write(f"**Storage Directory:** `{config.CHROMA_DIR.name}/`")
    st.write(f"**Total Reports Indexed:** `{len(indexed_sources)}`")
    if indexed_sources:
        with st.expander("View Indexed Files"):
            for s in indexed_sources:
                st.write(f"• `{s}`")

    if st.button("🗑️ Clear Vector Database", use_container_width=True):
        try:
            # Delete all documents from chroma
            all_data = db.get()
            if all_data and all_data.get("ids"):
                db.delete(ids=all_data["ids"])
            st.session_state.messages = []
            st.success("Database cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"Error clearing database: {e}")


# ================= MAIN CHAT AREA =================
st.markdown('<div class="main-header">Annual Report Q&A Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Financial analysis grounded strictly in company filings with page-numbered source citations.</div>',
    unsafe_allow_html=True,
)

# Pipeline Architecture Banner
with st.expander("ℹ️ How This Works (2-Phase Architecture)", expanded=False):
    st.markdown("""
    ```
    PDF Upload → Load Text (PyPDFLoader) → Chunk (1000/150) → Embed (Gemini) → ChromaDB
                                                                                  ↓
    User Question → Embed Query → Retrieve Top-K (k=4) → Prompt + Gemini 3.8 Flash → Answer + Citations
    ```
    - **Anti-Hallucination Rule:** Prompt enforces `Answer using ONLY the context. If not in context, say 'I could not find this in the report.'`
    - **Grounded Verification:** Every cited fact lists the exact page number from the filing.
    """)

# Quick Question Buttons (Section 6 from Spec)
st.write("**Suggested Finance Questions:**")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💰 FY2024 Revenue", use_container_width=True):
        st.session_state.quick_question = "What was the total revenue in FY2024?"
with col2:
    if st.button("⚠️ Management Risks", use_container_width=True):
        st.session_state.quick_question = "What are the main risks mentioned by management?"
with col3:
    if st.button("👥 Employee Count", use_container_width=True):
        st.session_state.quick_question = "How many employees does the company have?"
with col4:
    if st.button("📈 Dividend per Share", use_container_width=True):
        st.session_state.quick_question = "What is the dividend per share?"

# Render Chat History (Chat Memory feature)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "citations" in msg and msg["citations"]:
            st.markdown("**Citations:**")
            badge_html = "".join([
                f'<span class="citation-badge">📄 Page {c["page"]} ({c["source"]})</span>'
                for c in msg["citations"]
            ])
            st.markdown(badge_html, unsafe_allow_html=True)

        if "context_docs" in msg and msg["context_docs"]:
            with st.expander("🔍 View Retrieved Context Chunks"):
                for idx, doc in enumerate(msg["context_docs"], 1):
                    p = doc.get("page", "Unknown")
                    s = doc.get("source", "Report")
                    c = doc.get("content", "")
                    st.markdown(f"**Chunk {idx} — {s} (Page {p}):**")
                    st.text(c)
                    st.markdown("---")


# Process Input (either from quick question button or chat input box)
user_prompt = st.chat_input("Ask a question about the annual report...")

if st.session_state.quick_question:
    user_prompt = st.session_state.quick_question
    st.session_state.quick_question = None

if user_prompt:
    # Append user question
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Generate assistant answer
    with st.chat_message("assistant"):
        with st.spinner("Retrieving report sections and analyzing context..."):
            t_start = time.time()
            rag = FinancialRAGChain(
                vectorstore=db,
                model_name=selected_model,
                top_k=top_k,
            )

            try:
                res = rag.query(
                    question=user_prompt,
                    source_filter=active_filter,
                    k=top_k,
                    model_override=selected_model,
                )
                latency = round(time.time() - t_start, 2)
                ans = res["answer"]
                citations = res["citations"]
                model_used = res["model_used"]

                # Display answer
                st.markdown(ans)

                # Display Page Citations
                if citations:
                    st.markdown("**Citations:**")
                    badge_html = "".join([
                        f'<span class="citation-badge">📄 Page {c["page"]} ({c["source"]})</span>'
                        for c in citations
                    ])
                    badge_html += f'<span class="model-badge">⚡ {model_used} • {latency}s</span>'
                    st.markdown(badge_html, unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="model-badge">⚡ {model_used} • {latency}s</span>', unsafe_allow_html=True)

                # Context Inspector Accordion
                context_info = []
                if res["context_docs"]:
                    with st.expander("🔍 View Retrieved Context Chunks"):
                        for idx, doc in enumerate(res["context_docs"], 1):
                            p = doc.metadata.get("page", "Unknown")
                            s = doc.metadata.get("source", "Report")
                            st.markdown(f"**Chunk {idx} — {s} (Page {p}):**")
                            st.text(doc.page_content)
                            st.markdown("---")
                            context_info.append({
                                "page": p,
                                "source": s,
                                "content": doc.page_content,
                            })

                # Persist in session state for chat memory
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ans,
                    "citations": citations,
                    "context_docs": context_info,
                    "model_used": model_used,
                })

            except Exception as e:
                st.error(f"Error querying assistant: {e}")

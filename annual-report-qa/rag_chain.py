"""
RAG Chain Implementation for Annual Report Q&A Assistant.
Implements Steps 5 to 6 of the workflow:
Step 5: Retrieve top-k (k=4) relevant chunks for a question
Step 6: Generate answer using Gemini LLM (gemini-3.8-flash) and custom financial prompt
        Grounded strictly in retrieved context with page citations.
"""

import sys
from typing import List, Dict, Any, Optional, Tuple

import config
from ingest import get_vectorstore

from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI


def format_context_with_citations(docs: List[Document]) -> str:
    """
    Formats retrieved document chunks with clear page markers so the LLM
    can cite exact pages accurately.
    """
    formatted_chunks = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Report")
        page = doc.metadata.get("page", "Unknown")
        content = doc.page_content.strip()
        formatted_chunks.append(
            f"[Source: {source} | Page: {page}]\n{content}"
        )
    return "\n\n---\n\n".join(formatted_chunks)


def extract_content_text(content_obj: Any) -> str:
    """
    Robustly extracts textual response from LangChain AIMessage content,
    handling both string content and structured block lists.
    """
    if isinstance(content_obj, str):
        return content_obj

    if isinstance(content_obj, list):
        text_parts = []
        for item in content_obj:
            if isinstance(item, dict):
                # Handle thinking blocks or text blocks
                if item.get("type") == "text" and "text" in item:
                    text_parts.append(item["text"])
                elif "text" in item and item.get("type") != "thinking":
                    text_parts.append(item["text"])
            elif isinstance(item, str):
                text_parts.append(item)
        if text_parts:
            return "\n".join(text_parts)

    return str(content_obj)


def get_llm(model_name: Optional[str] = None) -> ChatGoogleGenerativeAI:
    """
    Initializes the Gemini LLM.
    Defaults to gemini-3.8-flash as specified by user.
    """
    selected_model = model_name or config.DEFAULT_GEMINI_MODEL
    api_key = config.GOOGLE_API_KEY
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Please add it to your .env file."
        )

    return ChatGoogleGenerativeAI(
        model=selected_model,
        google_api_key=api_key,
        temperature=0.1,  # Low temperature for strict factual accuracy
        max_retries=1,    # Fast failover if rate-limited or unavailable
    )


class FinancialRAGChain:
    """
    End-to-end RAG Chain for querying indexed annual reports.
    """
    def __init__(
        self,
        vectorstore=None,
        model_name: Optional[str] = None,
        top_k: int = config.TOP_K_CHUNKS,
    ):
        self.vectorstore = vectorstore or get_vectorstore()
        self.primary_model_name = model_name or config.DEFAULT_GEMINI_MODEL
        self.top_k = top_k
        self.prompt_template = PromptTemplate(
            template=config.FINANCIAL_QA_PROMPT,
            input_variables=["context", "question"],
        )

    def retrieve(
        self,
        question: str,
        source_filter: Optional[str] = None,
        k: Optional[int] = None,
    ) -> List[Document]:
        """
        Step 5: Retrieve top-k chunks for the question.
        Optionally filter by a specific PDF source file.
        """
        search_k = k or self.top_k
        filter_dict = {"source": source_filter} if source_filter else None

        if filter_dict:
            docs = self.vectorstore.similarity_search(
                query=question,
                k=search_k,
                filter=filter_dict,
            )
        else:
            docs = self.vectorstore.similarity_search(
                query=question,
                k=search_k,
            )
        return docs

    def query(
        self,
        question: str,
        source_filter: Optional[str] = None,
        k: Optional[int] = None,
        model_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Step 5 + 6: Retrieves top-k chunks, renders prompt, and generates grounded answer.
        Includes automatic fallback if the primary model encounters 429 quota or 503 unavailable.
        """
        retrieved_docs = self.retrieve(question, source_filter=source_filter, k=k)

        if not retrieved_docs:
            return {
                "question": question,
                "answer": "No relevant context found in the indexed reports. Please upload or index an annual report first.",
                "citations": [],
                "sources": [],
                "context_docs": [],
                "model_used": "none",
            }

        context_str = format_context_with_citations(retrieved_docs)
        formatted_prompt = self.prompt_template.format(
            context=context_str,
            question=question,
        )

        candidate_models = [model_override or self.primary_model_name]
        # Add fallback models if not already in candidates
        for fb in ["gemma-4-26b-a4b-it", "gemini-3.7-flash", "gemini-flash-latest"]:
            if fb not in candidate_models:
                candidate_models.append(fb)

        last_error = None
        answer_text = ""
        model_used = candidate_models[0]

        for model in candidate_models:
            try:
                llm = get_llm(model_name=model)
                response = llm.invoke(formatted_prompt)
                answer_text = extract_content_text(response.content)
                model_used = model
                break
            except Exception as e:
                last_error = e
                error_msg = str(e)
                # If rate-limited (429) or high-demand (503), try next available model in list
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "503" in error_msg or "UNAVAILABLE" in error_msg:
                    continue
                else:
                    # Non-retryable error
                    raise e

        if not answer_text and last_error:
            raise last_error

        # Gather unique page citations
        citations = []
        seen_pages = set()
        for doc in retrieved_docs:
            page = doc.metadata.get("page")
            source = doc.metadata.get("source", "Report")
            key = (source, page)
            if key not in seen_pages:
                seen_pages.add(key)
                citations.append({
                    "page": page,
                    "source": source,
                    "snippet": doc.page_content[:250].strip() + "...",
                })

        return {
            "question": question,
            "answer": answer_text,
            "citations": citations,
            "sources": sorted(list({c['page'] for c in citations if c.get('page') is not None})),
            "context_docs": retrieved_docs,
            "model_used": model_used,
        }


def ask_report(
    question: str,
    source_filter: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to query the RAG chain.
    """
    rag = FinancialRAGChain(model_name=model_name)
    return rag.query(question, source_filter=source_filter)


if __name__ == "__main__":
    test_question = sys.argv[1] if len(sys.argv) > 1 else "What was the total revenue in FY2024?"
    print(f"\nQuestion: {test_question}")
    rag = FinancialRAGChain()
    result = rag.query(test_question)
    print(f"\nModel Used: {result['model_used']}")
    print(f"Citations: Pages {result['sources']}")
    print(f"\nAnswer:\n{result['answer']}")

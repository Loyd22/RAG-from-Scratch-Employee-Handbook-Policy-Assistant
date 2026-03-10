"""
api/deps.py
Dependency injection for services.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from backend.app.rag.embeddings.embedder import Embedder
from backend.app.rag.llm.client import LLMClient
from backend.app.repositories.vector_store import ChromaVectorStore
from backend.app.services.rag_service import RAGService


def get_rag_service() -> RAGService:
    """Create and return a configured RAGService instance."""
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing in .env")

    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()
    chat_model = os.getenv("CHAT_MODEL", "gpt-4o-mini").strip()

    chroma_dir = os.getenv("CHROMA_DIR", "data/indexes/chroma").strip()
    chroma_collection = os.getenv("CHROMA_COLLECTION", "employee_handbook").strip()

    top_k = int(os.getenv("TOP_K", "5"))
    min_results = int(os.getenv("MIN_RESULTS", "3"))

    repo_root = Path(__file__).resolve().parents[3]
    chroma_path = (repo_root / chroma_dir).resolve()

    embedder = Embedder(api_key=api_key, model=embedding_model)
    llm = LLMClient(api_key=api_key, chat_model=chat_model)
    store = ChromaVectorStore(chroma_dir=chroma_path, collection_name=chroma_collection)

    distance_threshold = float(os.getenv("DISTANCE_THRESHOLD", "0.35"))
    max_context_chars = int(os.getenv("MAX_CONTEXT_CHARS", "12000"))
    llm_retry_count = int(os.getenv("LLM_RETRY_COUNT", "1"))

    return RAGService(
    embedder=embedder,
    vector_store=store,
    llm=llm,
    top_k=top_k,
    min_results=min_results,
    distance_threshold=distance_threshold,
    max_context_chars=max_context_chars,
    llm_retry_count=llm_retry_count,
)
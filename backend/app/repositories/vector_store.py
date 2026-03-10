"""
repositories/vector_store.py
Vector store repository for Chroma operations (query only for now).

NON-PROGRAMMER EXPLANATION
--------------------------
This file is the "library search desk" for your RAG system.

- Your Chroma database (data/indexes/chroma) already contains many text chunks from the PDF,
  and each chunk has a "meaning fingerprint" (embedding vector).
- When a user asks a question, we also convert the question into an embedding vector.
- This class sends that question vector to Chroma and asks:
  "Give me the top K chunks that are most similar in meaning."

What you get back from this query:
- documents: the actual chunk texts (the content we will show the AI as context)
- metadatas: information about where each chunk came from (doc_name + page_number)
             so we can cite the source pages
- distances: similarity scores (how close the chunk meaning is to the question meaning)
             smaller distance usually means more relevant

Why this file exists (Separation of Concerns):
- Your service layer should not care how Chroma works internally.
- If you switch from Chroma to FAISS later, you only change this repository file,
  not the rest of your RAG logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import chromadb


class ChromaVectorStore:
    """Repository wrapper for querying a persistent Chroma collection."""

    def __init__(self, chroma_dir: Path, collection_name: str) -> None:
        """Initialize persistent Chroma client and collection."""
        # Creates (or opens) a Chroma database stored on disk at `chroma_dir`.
        self._client = chromadb.PersistentClient(path=str(chroma_dir))

        # Opens the specific "collection" (like a table) that contains your indexed chunks.
        self._collection = self._client.get_collection(name=collection_name)

    def query(
        self,
        query_embedding: List[float],
        top_k: int,
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """
        Query Chroma collection by embedding.

        Simple meaning:
        - query_embedding = the "meaning fingerprint" of the user's question
        - top_k = how many best matching chunks we want back

        Returns:
            distances: list of similarity scores (smaller often means closer/more relevant)
            metadatas: list of metadata dicts (doc_name, page_number) used for citations
            documents: list of chunk texts (the actual content we feed into the LLM)
        """
        # Ask Chroma to find the nearest chunks (by meaning) to the question embedding.
        res = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Chroma returns nested lists because it supports querying multiple questions at once.
        # We only query one question, so we take the first list ([0]).
        distances = res.get("distances", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]
        documents = res.get("documents", [[]])[0]

        # Return the three pieces needed by the RAG pipeline:
        # - similarity scores, source info, and actual texts.
        return distances, metadatas, documents
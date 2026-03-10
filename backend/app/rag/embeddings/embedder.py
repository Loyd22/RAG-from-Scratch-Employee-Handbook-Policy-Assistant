"""
rag/embeddings/embedder.py
OpenAI embeddings wrapper for producing query vectors.

NON-PROGRAMMER EXPLANATION
--------------------------
This file turns a piece of text (usually a user's question) into an "embedding".

What is an embedding (simple):
- An embedding is a list of numbers that represents the *meaning* of the text.
- Think of it like a "meaning code" or "meaning fingerprint".

Why we need this:
- Your Chroma database stores embeddings for all document chunks.
- To search the database by meaning, the user's question must also be converted into an embedding.
- Then Chroma can compare the question embedding to chunk embeddings and find the closest matches.

What this class does:
- Stores your OpenAI API key and embedding model once (setup).
- Provides one method: embed_query(text) -> returns the embedding vector for that text.
"""

from __future__ import annotations

from typing import List

from openai import OpenAI


class Embedder:
    """Wrapper for OpenAI embeddings endpoint."""

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize embedder with API key and embedding model."""
        # Creates an OpenAI client using your API key (so we can call the embeddings API).
        self._client = OpenAI(api_key=api_key)

        # Stores the embedding model name, e.g., "text-embedding-3-small".
        self._model = model

    def embed_query(self, text: str) -> List[float]:
        """Embed a query string into a vector."""
        # Replace newlines with spaces to keep the input clean and consistent.
        # (Newlines can cause weird formatting; embeddings work better with normalized text.)
        safe_text = text.replace("\n", " ")

        # Call OpenAI embeddings API:
        # - input is the question text
        # - output is a vector (list of numbers) that represents the meaning of that text
        resp = self._client.embeddings.create(model=self._model, input=safe_text)

        # Return the embedding vector for the first (and only) input text.
        return resp.data[0].embedding
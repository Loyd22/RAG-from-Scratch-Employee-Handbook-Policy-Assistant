"""
scripts/test_retrieval.py
Quick retrieval smoke-test for the Chroma index (no LLM yet).
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


def main() -> None:
    """Query the vector store and print top matches."""
    load_dotenv()

    oa = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "").strip())
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()
    chroma_dir = os.getenv("CHROMA_DIR", "data/indexes/chroma").strip()
    collection_name = os.getenv("CHROMA_COLLECTION", "employee_handbook").strip()

    ch_client = chromadb.PersistentClient(path=str((ROOT_DIR / chroma_dir).resolve()))
    collection = ch_client.get_collection(name=collection_name)

    question = "What is the paid time off policy?"
    q_vec = oa.embeddings.create(model=model, input=question).data[0].embedding

    res = collection.query(query_embeddings=[q_vec], n_results=5, include=["documents", "metadatas", "distances"])
    for i in range(5):
        print("\n---")
        print("id:", res["ids"][0][i])
        print("meta:", res["metadatas"][0][i])
        print("text:", res["documents"][0][i][:300], "...")


if __name__ == "__main__":
    main()
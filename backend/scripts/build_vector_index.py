"""
scripts/build_vector_index.py
Create embeddings for chunks.jsonl and store them in a persistent Chroma vector DB.

This is Step 6 of the RAG build: embeddings + vector store index.

-----------------------------------------------------------------
Think of your PDF chunks like many small notes from a book.

Goal:
1) Turn every note (chunk text) into a "meaning fingerprint" (embedding = numbers).
2) Save those fingerprints into a "meaning search database" (Chroma).
3) Later, when you ask a question, your system can quickly find the most relevant notes
   by meaning (not just matching keywords).

What you need before running:
- data/processed/chunks.jsonl (created by your earlier scripts)
- a valid OPENAI_API_KEY in your .env file

What you get after running:
- a persistent Chroma database folder (default: data/indexes/chroma)
- a collection (default: "employee_handbook") containing:
  - chunk_id (unique id)
  - chunk text
  - embedding numbers
  - metadata (doc_name, page_number for citations)

How the script works (high-level steps):
A) Load your API key and settings from .env
B) Read all chunks from chunks.jsonl
C) Send chunk texts to OpenAI Embeddings API in batches
D) Store embeddings + text + metadata in Chroma so retrieval is fast
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI
import chromadb


# Where the project root folder is located on your computer.
# This helps the script find files reliably even if you run it from different terminals.
ROOT_DIR = Path(__file__).resolve().parents[2]

# This is the file created earlier that contains all text chunks (small pieces of the PDF).
CHUNKS_PATH = ROOT_DIR / "data" / "processed" / "chunks.jsonl"


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """
    READ INPUT DATA FILE (simple meaning)
    - Opens a JSONL file (JSON Lines).
    - Each line is one record (one chunk).
    - Returns all records as a list you can loop through.

    If you imagine the file as a notebook:
    - Each line is one note.
    - This function collects all notes into a stack.
    """
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def batch_list(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    SPLIT INTO SMALL GROUPS (batching)
    - APIs often have limits and are faster/safer when you send data in small batches.
    - This function breaks one big list into many smaller lists.

    Analogy:
    - Instead of sending 1000 messages at once,
      you send 32 at a time to avoid overload.
    """
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def get_embeddings(client: OpenAI, model: str, texts: List[str]) -> List[List[float]]:
    """
    CREATE MEANING FINGERPRINTS (embeddings)
    - Sends a list of texts to OpenAI Embeddings API.
    - Receives a list of vectors (numbers) back.
    - Each vector represents the meaning of one text.

    Why replace newlines:
    - Newlines can sometimes produce odd formatting/tokenization.
    - Replacing them with spaces makes embeddings more consistent.
    """
    safe_texts = [t.replace("\n", " ") for t in texts]
    resp = client.embeddings.create(model=model, input=safe_texts)
    return [item.embedding for item in resp.data]


def main() -> None:
    """
    MAIN WORKFLOW (what happens when you run the script)

    1) Load environment variables from .env
       - OPENAI_API_KEY (required)
       - EMBEDDING_MODEL (optional, default used if missing)
       - CHROMA_DIR (where to store the database files)
       - CHROMA_COLLECTION (collection name inside Chroma)

    2) Read chunks.jsonl
       - Each chunk has chunk_id, text, doc_name, page_number.

    3) Prepare payloads
       - ids: unique IDs (so each chunk can be referenced later)
       - documents: the chunk texts
       - metadatas: extra info used for citations and filtering

    4) Create clients
       - OpenAI client: to generate embeddings
       - Chroma client: to store embeddings in a persistent folder

    5) (Optional) Clear old collection
       - Prevent duplicates if you rebuild the index.
       - If delete fails (version differences), we continue and upsert/add anyway.

    6) Embed in batches, then store in Chroma
       - Send 32 chunks at a time
       - Retry up to 3 times if network/API temporarily fails

    7) Print a success message
       - Shows how many chunks were indexed and where the DB lives.
    """
    load_dotenv()

    # Read OpenAI API key from .env so it is not hardcoded in your code.
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in .env")

    # Choose which embedding model to use (default is a good cheap one).
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()

    # Folder where Chroma will store its persistent data (like a database folder).
    chroma_dir = os.getenv("CHROMA_DIR", "data/indexes/chroma").strip()

    # Collection name inside Chroma (like a table name).
    collection_name = os.getenv("CHROMA_COLLECTION", "employee_handbook").strip()

    # Make sure the input chunks file exists.
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Input not found: {CHUNKS_PATH}")

    # Load all chunks from disk into memory.
    chunks = read_jsonl(CHUNKS_PATH)

    # Prepare three lists that Chroma needs:
    # - ids: unique names for each chunk
    # - documents: the actual chunk text
    # - metadatas: small extra details (useful for citations like page number)
    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for rec in chunks:
        ids.append(str(rec["chunk_id"]))
        documents.append(str(rec["text"]))
        metadatas.append(
            {
                "doc_name": rec.get("doc_name", ""),
                "page_number": int(rec.get("page_number", 0)),
            }
        )

    # Create OpenAI client (used to generate embeddings).
    oa = OpenAI(api_key=api_key)

    # Create or reuse the folder where Chroma will store its database files.
    chroma_path = (ROOT_DIR / chroma_dir).resolve()
    chroma_path.mkdir(parents=True, exist_ok=True)

    # Create a persistent Chroma client pointing to that folder.
    ch_client = chromadb.PersistentClient(path=str(chroma_path))

    # Get or create the collection where embeddings will be stored.
    collection = ch_client.get_or_create_collection(name=collection_name)

    # Optional reset: try to delete and recreate the collection so you don't duplicate data.
    # (Some Chroma versions may not support this smoothly, so we catch errors.)
    try:
        ch_client.delete_collection(name=collection_name)
        collection = ch_client.get_or_create_collection(name=collection_name)
    except Exception:
        # If deletion fails, we just continue and add.
        pass

    # Split all chunks into small batches for the embedding API.
    BATCH_SIZE = 32
    id_batches = batch_list(ids, BATCH_SIZE)
    doc_batches = batch_list(documents, BATCH_SIZE)
    meta_batches = batch_list(metadatas, BATCH_SIZE)

    total = 0

    # For each batch:
    # - create embeddings using OpenAI
    # - store everything into Chroma
    for b_ids, b_docs, b_meta in zip(id_batches, doc_batches, meta_batches):
        # Retry up to 3 times in case of temporary network/API issues.
        for attempt in range(1, 4):
            try:
                vectors = get_embeddings(oa, embedding_model, b_docs)
                collection.add(
                    ids=b_ids,
                    documents=b_docs,
                    embeddings=vectors,
                    metadatas=b_meta,
                )
                total += len(b_ids)
                break
            except Exception:
                # Wait a bit longer each retry (simple backoff).
                if attempt == 3:
                    raise
                time.sleep(1.5 * attempt)

    # Final summary print so you know it worked and where the index was stored.
    print(f"✅ Embedded and indexed {total} chunks into Chroma:")
    print(f"   - collection: {collection_name}")
    print(f"   - dir:        {chroma_path}")


if __name__ == "__main__":
    # When you run: python scripts/build_vector_index.py
    # this is the function that starts everything.
    main()
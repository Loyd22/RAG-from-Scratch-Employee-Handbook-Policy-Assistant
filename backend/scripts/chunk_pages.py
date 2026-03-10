"""
scripts/chunk_pages.py
Split cleaned pages into overlapping chunks and save as JSONL.

WHAT THIS SCRIPT DOES (simple explanation):
- Reads per-page cleaned text records from: data/processed/pages_clean.jsonl
  Each line is expected to look like:
  {"doc_name":"...pdf","page_number":1,"text":"...clean page text..."}

- For every page's text, it cuts the text into multiple smaller pieces called "chunks"
  using a fixed character window (CHUNK_SIZE) with overlap (CHUNK_OVERLAP).
  Overlap means the next chunk repeats the last part of the previous chunk, so important
  sentences that sit near a boundary are not lost.

- Writes the chunked output to: data/processed/chunks.jsonl
  Each output line looks like:
  {
    "chunk_id": "<doc_name>:p<page_number>:c<chunk_index>",
    "doc_name": "...",
    "page_number": 1,
    "text": "...chunk text..."
  }

WHY THIS IS NEEDED (for RAG):
- LLM retrieval works better on smaller, focused pieces of text rather than whole pages.
- These chunks are what you will embed into vectors and store in FAISS/Chroma.
- Later, when a user asks a question, you retrieve the most relevant chunks and cite
  their page numbers.

NOTES:
- This is an MVP chunker: character-based, not sentence-aware.
- If you want higher quality, later you can chunk by headings/sentences/tokens.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


ROOT_DIR = Path(__file__).resolve().parents[2]
IN_PATH = ROOT_DIR / "data" / "processed" / "pages_clean.jsonl"
OUT_PATH = ROOT_DIR / "data" / "processed" / "chunks.jsonl"

# Chunking settings (character-based MVP)
CHUNK_SIZE = 1200         # characters per chunk
CHUNK_OVERLAP = 250       # characters of overlap between chunks


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read JSONL into list of records."""
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def write_jsonl(records: List[Dict[str, Any]], path: Path) -> None:
    """Write list of records to JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Chunk text into overlapping windows."""
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end == text_len:
            break

        start = max(0, end - overlap)

    return chunks


def main() -> None:
    """Create chunks.jsonl from pages_clean.jsonl."""
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Input not found: {IN_PATH}")

    pages = read_jsonl(IN_PATH)
    out: List[Dict[str, Any]] = []

    for page in pages:
        doc_name = page.get("doc_name", "")
        page_number = int(page.get("page_number", 0))
        text = page.get("text", "")

        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)

        for i, chunk in enumerate(chunks, start=1):
            out.append(
                {
                    "chunk_id": f"{doc_name}:p{page_number}:c{i}",
                    "doc_name": doc_name,
                    "page_number": page_number,
                    "text": chunk,
                }
            )

    write_jsonl(out, OUT_PATH)
    print(f"✅ Wrote {len(out)} chunks to {OUT_PATH}")


if __name__ == "__main__":
    main()
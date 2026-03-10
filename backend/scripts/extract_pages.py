"""
scripts/extract_pages.py
Extract text from each PDF page and save as JSONL for downstream chunking and citations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from pypdf import PdfReader

ROOT_DIR = Path(__file__).resolve().parents[2]  # repo root
PDF_PATH = ROOT_DIR / "data" / "raw" / "employee_handbook.pdf"
OUT_PATH = ROOT_DIR / "data" / "processed" / "pages.jsonl"


def extract_pages(pdf_path: Path) -> list[Dict[str, Any]]:
    """Extract per-page text records from a PDF."""
    reader = PdfReader(str(pdf_path))
    records: list[Dict[str, Any]] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        records.append(
            {
                "doc_name": pdf_path.name,
                "page_number": page_number,
                "text": text.strip(),
            }
        )

    return records


def write_jsonl(records: list[Dict[str, Any]], out_path: Path) -> None:
    """Write records to JSONL (one JSON object per line)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> None:
    """Run extraction and save output."""
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found at: {PDF_PATH}")

    records = extract_pages(PDF_PATH)
    write_jsonl(records, OUT_PATH)
    print(f"✅ Wrote {len(records)} pages to {OUT_PATH}")


if __name__ == "__main__":
    main()
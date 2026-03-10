"""
scripts/clean_pages.py
Normalize extracted PDF page text and save to a clean JSONL file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict


ROOT_DIR = Path(__file__).resolve().parents[2]
IN_PATH = ROOT_DIR / "data" / "processed" / "pages.jsonl"
OUT_PATH = ROOT_DIR / "data" / "processed" / "pages_clean.jsonl"


def clean_text(text: str) -> str:
    """Clean PDF-extracted text while preserving meaning."""
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove hyphenation at line breaks: "employ-\nee" -> "employee"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Convert single newlines to spaces (keep paragraph breaks)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Collapse multiple newlines into a paragraph break
    text = re.sub(r"\n{2,}", "\n\n", text)

    # Collapse repeated whitespace
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


def read_jsonl(path: Path) -> list[Dict[str, Any]]:
    """Read JSONL file into a list of dict records."""
    records: list[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def write_jsonl(records: list[Dict[str, Any]], path: Path) -> None:
    """Write records to JSONL (one JSON object per line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> None:
    """Run cleaning pipeline."""
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Input not found: {IN_PATH}")

    pages = read_jsonl(IN_PATH)
    cleaned: list[Dict[str, Any]] = []

    for rec in pages:
        cleaned.append(
            {
                "doc_name": rec.get("doc_name", ""),
                "page_number": rec.get("page_number", 0),
                "text": clean_text(rec.get("text", "")),
            }
        )

    write_jsonl(cleaned, OUT_PATH)
    print(f"✅ Cleaned {len(cleaned)} pages -> {OUT_PATH}")


if __name__ == "__main__":
    main()
"""
scripts/run_eval.py
Runs an evaluation set against the local /api/v1/ask endpoint and writes report.json.

This script is designed to be "fail-loud" and always attempt to write a report
even if some questions fail.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
QUESTIONS_PATH = ROOT_DIR / "data" / "eval" / "questions.jsonl"
REPORT_PATH = ROOT_DIR / "data" / "eval" / "report.json"

ASK_URL = "http://127.0.0.1:8000/api/v1/ask"


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read JSONL file into a list of dicts."""
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def main() -> None:
    """Run evaluation and write a JSON report."""
    if not QUESTIONS_PATH.exists():
        raise FileNotFoundError(f"Missing questions file: {QUESTIONS_PATH}")

    questions = read_jsonl(QUESTIONS_PATH)
    if not questions:
        raise RuntimeError("questions.jsonl is empty. Add at least 1 question.")

    results: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    correct = 0
    found_with_citations = 0
    not_found_correct = 0
    not_found_total = 0

    start_all = time.time()

    for q in questions:
        qid = q.get("id", "")
        question = q.get("question", "")
        expected = str(q.get("expected_verdict", "")).strip().upper()

        t0 = time.time()
        row: Dict[str, Any] = {
            "id": qid,
            "question": question,
            "expected_verdict": expected,
        }

        try:
            resp = requests.post(ASK_URL, json={"question": question}, timeout=60)
            row["http_status"] = resp.status_code
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"raw": resp.text}
            row["response"] = data
        except Exception as e:
            row["http_status"] = None
            row["response"] = {"error": str(e)}
            data = {"verdict": "ERROR", "citations": []}

        row["latency_ms"] = int((time.time() - t0) * 1000)

        actual = str(data.get("verdict", "ERROR")).strip().upper()
        citations = data.get("citations", [])

        row["actual_verdict"] = actual
        row["citations_count"] = len(citations) if isinstance(citations, list) else 0

        is_correct = (actual == expected)
        row["is_correct"] = is_correct

        if expected == "NOT_FOUND":
            not_found_total += 1
            if actual == "NOT_FOUND":
                not_found_correct += 1

        if actual == "FOUND" and isinstance(citations, list) and len(citations) > 0:
            found_with_citations += 1

        if is_correct:
            correct += 1
        else:
            failures.append(
                {
                    "id": qid,
                    "question": question,
                    "expected_verdict": expected,
                    "actual_verdict": actual,
                    "http_status": row["http_status"],
                    "response_preview": str(row.get("response", ""))[:500],
                }
            )

        results.append(row)

    total = len(questions)
    duration_ms = int((time.time() - start_all) * 1000)

    report: Dict[str, Any] = {
        "summary": {
            "total": total,
            "correct": correct,
            "accuracy": round(correct / total, 4),
            "found_with_citations": found_with_citations,
            "not_found_total": not_found_total,
            "not_found_correct": not_found_correct,
            "not_found_accuracy": round((not_found_correct / not_found_total), 4) if not_found_total > 0 else None,
            "duration_ms": duration_ms,
            "ask_url": ASK_URL,
        },
        "failures": failures,
        "results": results,  # keep for debugging; you can remove later if too large
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ Wrote report: {REPORT_PATH}")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
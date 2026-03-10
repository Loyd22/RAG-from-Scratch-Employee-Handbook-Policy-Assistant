"""
rag/prompting/templates.py
Prompt templates for RAG generation with strict JSON output.
"""


from __future__ import annotations

def build_system_prompt() -> str:
    """Return the system prompt enforcing grounded answers and JSON-only output."""
    return (
        "You are a policy assistant. Answer ONLY using the provided CONTEXT.\n"
        "If the answer is not explicitly present in CONTEXT, return verdict NOT_FOUND.\n"
        "Do not guess. Do not use external knowledge.\n\n"
        "Output MUST be valid JSON ONLY (no markdown, no extra text) with this schema:\n"
        "{\n"
        '  "verdict": "FOUND" | "NOT_FOUND",\n'
        '  "answer": string,\n'
        '  "citations": [{"doc_name": string, "page_number": integer}]\n'
        "}\n\n"
        "Citations must reference ONLY the pages present in CONTEXT.\n"
        "If verdict is NOT_FOUND, citations must be an empty list.\n"
    )

def build_user_prompt(question: str, context: str) -> str:
    """Return the user prompt containing question and retrieved context."""

    return (
        f"QUESTION:\n{question}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "Return JSON only."
    )



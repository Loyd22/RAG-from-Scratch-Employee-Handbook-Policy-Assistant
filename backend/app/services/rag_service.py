"""
services/rag_service.py
RAG orchestration: retrieve chunks, build prompt, generate grounded answer with citations.

Step 8 additions:
- Retrieval confidence gate (distance threshold)
- Context size cap
- LLM retry (fail closed)
- Basic logging for observability
- Citation fallback (auto-cite from retrieved context if LLM citations are missing/invalid)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Set, Tuple

from backend.app.schemas.ask import AskResponse
from backend.app.schemas.common import Citation
from backend.app.rag.prompting.templates import build_system_prompt, build_user_prompt
from backend.app.rag.llm.client import LLMClient
from backend.app.rag.embeddings.embedder import Embedder
from backend.app.repositories.vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class RAGService:
    """Service that handles the end-to-end RAG answering flow."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: ChromaVectorStore,
        llm: LLMClient,
        top_k: int,
        min_results: int,
        distance_threshold: float,
        max_context_chars: int,
        llm_retry_count: int,
    ) -> None:
        """Initialize dependencies and reliability thresholds."""
        self._embedder = embedder
        self._vector_store = vector_store
        self._llm = llm
        self._top_k = top_k
        self._min_results = min_results
        self._distance_threshold = distance_threshold
        self._max_context_chars = max_context_chars
        self._llm_retry_count = llm_retry_count

    def answer(self, question: str) -> AskResponse:
        """
        Answer a user question using retrieval + LLM generation.

        Fail-closed behavior:
        - If retrieval is weak, return NOT_FOUND
        - If LLM returns invalid JSON, retry a limited number of times then return NOT_FOUND
        - If citations are invalid, use a safe fallback based on retrieved context
        """
        q_vec = self._embedder.embed_query(question)

        distances, metadatas, documents = self._vector_store.query(q_vec, top_k=self._top_k)

        usable_docs = [d for d in documents if isinstance(d, str) and d.strip()]
        usable_meta = [m for m in metadatas if isinstance(m, dict)]

        # Observability: log retrieval summary (top pages + distances)
        self._log_retrieval(question=question, distances=distances, metadatas=usable_meta)

        # Gate 1: minimum retrieval results
        if len(usable_docs) < self._min_results:
            return AskResponse(verdict="NOT_FOUND", answer="Not found in the handbook.", citations=[])

        # Gate 2: distance threshold (confidence gate)
        best_distance = self._best_distance(distances)
        if best_distance is None:
            return AskResponse(verdict="NOT_FOUND", answer="Not found in the handbook.", citations=[])

        # Chroma distances: smaller is typically better. We treat large distance as weak match.
        if best_distance > self._distance_threshold:
            logger.info(
                "RAG gate: best_distance too weak",
                extra={"best_distance": best_distance, "threshold": self._distance_threshold},
            )
            return AskResponse(verdict="NOT_FOUND", answer="Not found in the handbook.", citations=[])

        context, allowed_citations = self._build_context(usable_docs, usable_meta)

        # Gate 3: cap context size to avoid bloating the prompt
        context = self._trim_context(context, self._max_context_chars)

        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(question=question, context=context)

        raw: Dict[str, Any] | None = None
        attempts = max(0, self._llm_retry_count) + 1

        for attempt in range(1, attempts + 1):
            try:
                raw = self._llm.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
                logger.info("RAG raw LLM output", extra={"raw": raw})
                break
            except Exception as exc:
                logger.warning(
                    "LLM JSON generation failed",
                    extra={"attempt": attempt, "attempts": attempts, "error": str(exc)[:300]},
                )
                raw = None

        if raw is None:
            return AskResponse(verdict="NOT_FOUND", answer="Not found in the handbook.", citations=[])

        response = self._validate_and_convert(raw=raw, allowed=allowed_citations)

        # Observability: log final verdict and citations
        logger.info(
            "RAG answer complete",
            extra={
                "verdict": response.verdict,
                "citations": [{"doc": c.doc_name, "page": c.page_number} for c in response.citations],
            },
        )
        return response

    def _best_distance(self, distances: List[Any]) -> float | None:
        """Return the best (smallest) distance if present and numeric."""
        if not distances:
            return None
        numeric: List[float] = []
        for d in distances:
            try:
                numeric.append(float(d))
            except Exception:
                continue
        if not numeric:
            return None
        return min(numeric)

    def _trim_context(self, context: str, max_chars: int) -> str:
        """Trim context to a maximum number of characters."""
        if max_chars <= 0:
            return context
        if len(context) <= max_chars:
            return context
        return context[:max_chars].rstrip()

    def _log_retrieval(self, question: str, distances: List[Any], metadatas: List[Dict[str, Any]]) -> None:
        """Log a compact retrieval trace (pages and distances) for debugging."""
        try:
            top = []
            for i in range(min(len(metadatas), len(distances), 5)):
                meta = metadatas[i]
                top.append(
                    {
                        "doc": meta.get("doc_name", ""),
                        "page": int(meta.get("page_number", 0)),
                        "distance": float(distances[i]) if i < len(distances) else None,
                    }
                )
            logger.info("RAG retrieval", extra={"question": question[:200], "top": top})
        except Exception:
            # Never break the pipeline due to logging
            pass

    def _build_context(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> Tuple[str, Set[Tuple[str, int]]]:
        """
        Build the CONTEXT string for the LLM and compute allowed citations.

        Returns:
            context: formatted context blocks
            allowed: set of (doc_name, page_number) pairs present in retrieved results
        """
        blocks: List[str] = []
        allowed: Set[Tuple[str, int]] = set()

        for i, (doc, meta) in enumerate(zip(documents, metadatas), start=1):
            doc_name = str(meta.get("doc_name", "")).strip()
            page_number = int(meta.get("page_number", 0))

            if doc_name and page_number >= 1:
                allowed.add((doc_name, page_number))

            blocks.append(
                f"[{i}] doc_name={doc_name} page_number={page_number}\n"
                f"{doc.strip()}\n"
            )

        return "\n".join(blocks).strip(), allowed

    def _validate_and_convert(self, raw: Dict[str, Any], allowed: Set[Tuple[str, int]]) -> AskResponse:
        """
        Validate model JSON and enforce citation constraints.

        Step 8 improvement:
        - If model returns FOUND but citations are missing/invalid, auto-cite from retrieved context
          instead of failing to NOT_FOUND.
        """
        verdict = str(raw.get("verdict", "")).strip().upper()
        answer = str(raw.get("answer", "")).strip()
        citations_raw = raw.get("citations", [])

        if verdict not in {"FOUND", "NOT_FOUND"}:
            return AskResponse(verdict="NOT_FOUND", answer="Not found in the handbook.", citations=[])

        if verdict == "NOT_FOUND":
            return AskResponse(verdict="NOT_FOUND", answer="Not found in the handbook.", citations=[])

        # verdict == FOUND
        if not answer:
            return AskResponse(verdict="NOT_FOUND", answer="Not found in the handbook.", citations=[])

        citations: List[Citation] = []
        seen: Set[Tuple[str, int]] = set()

        if isinstance(citations_raw, list):
            for item in citations_raw:
                if not isinstance(item, dict):
                    continue

                doc_name = str(item.get("doc_name", "")).strip()
                try:
                    page_number = int(item.get("page_number", 0))
                except Exception:
                    continue

                key = (doc_name, page_number)
                if key in seen:
                    continue

                if key in allowed:
                    seen.add(key)
                    citations.append(Citation(doc_name=doc_name, page_number=page_number))

        # NEW: fallback auto-citations from retrieved context
        if not citations:
            fallback = sorted(list(allowed))[:2]  # pick first 1–2 retrieved pages
            if fallback:
                citations = [Citation(doc_name=d, page_number=p) for d, p in fallback]
                logger.info("RAG citation fallback used", extra={"fallback": fallback})
                return AskResponse(verdict="FOUND", answer=answer, citations=citations)

            # If we have no allowed citations at all, fail closed.
            return AskResponse(verdict="NOT_FOUND", answer="Not found in the handbook.", citations=[])

        return AskResponse(verdict="FOUND", answer=answer, citations=citations)
"""
api/v1/endpoints/ask.py
POST /ask endpoint that returns grounded answers with citations.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.schemas.ask import AskRequest, AskResponse
from backend.app.services.rag_service import RAGService
from backend.app.api.deps import get_rag_service

router = APIRouter()


@router.post("/ask", response_model=AskResponse, tags=["rag"])
def ask_question(payload: AskRequest, rag: RAGService = Depends(get_rag_service)) -> AskResponse:
    """Answer a question using the RAG pipeline."""
    return rag.answer(payload.question) 
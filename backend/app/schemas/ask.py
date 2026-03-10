"""
schemas/ask.py
Request/response models for the /ask endpoint.
"""


from __future__ import annotations
from typing import List, Literal 
from pydantic import BaseModel, Field 
from .common import Citation

Vertict = Literal["FOUND", "NOT_FOUND"]

class AskRequest(BaseModel):
    """Incoming request to ask a question against the RAG knowledge base."""
    

    question: str = Field(..., min_length=3, description="User question")


class AskResponse(BaseModel):
    """RAG response containing grounded answer, citations, and verdict."""
    
    verdict: Vertict = Field(..., description="FOUND if answer is supported; else NOT_FOUND")
    answer: str = Field(..., description="Final answer text")
    citations: List[Citation] = Field(default_factory=list, description="List of source citati")
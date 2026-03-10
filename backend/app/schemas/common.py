"""
schemas/common.py
Shared Pydantic models used across endpoints.
"""


from __future__ import annotations
from pydantic import BaseModel, Field 

class Citation(BaseModel):
    """A citation pointing to a source document and page number."""

    doc_name: str = Field(..., description="Source document filename")
    page_number: int = Field(..., ge=1, description="1-indexed page number")



class ErrorResponse(BaseModel):
     """Standard error response payload."""


     detail: str = Field(..., description="Error description")
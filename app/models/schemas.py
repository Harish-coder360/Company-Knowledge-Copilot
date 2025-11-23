"""Pydantic schemas for API endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SourceMetadata(BaseModel):
    source_id: Optional[str] = None
    source_type: str
    file_name: Optional[str] = None
    url: Optional[str] = None
    content_type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IngestURLRequest(BaseModel):
    urls: List[str]
    tags: Optional[List[str]] = None


class ChatRequest(BaseModel):
    message: str
    source_type: Optional[str] = Field(default=None, description="Filter by source type")
    top_k: Optional[int] = Field(default=None, description="Override retrieval depth")
    enable_mcp: bool = Field(default=False, description="Trigger MCP augmentation")


class ChatResponseSource(BaseModel):
    name: str
    source_type: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatResponseSource]


class SourceListItem(BaseModel):
    name: str
    source_type: str
    created_at: datetime


class IngestResponse(BaseModel):
    inserted: int
    source_type: str

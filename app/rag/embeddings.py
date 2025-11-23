"""Embedding utilities using an OpenAI-compatible API."""
from __future__ import annotations

from typing import List

from openai import OpenAI

from app.core.config import settings


class EmbeddingClient:
    """Thin wrapper around OpenAI embeddings for dependency injection."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self.model = model
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for embeddings")
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_api_base)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts."""

        if not texts:
            return []
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]

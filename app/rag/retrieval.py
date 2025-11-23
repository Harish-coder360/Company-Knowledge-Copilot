"""Retrieval and context building utilities."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.core.config import settings
from app.rag.vectorstore import VectorStore


class Retriever:
    """Encapsulates similarity search and context window assembly."""

    def __init__(self, store: Optional[VectorStore] = None) -> None:
        self.store = store or VectorStore()

    def fetch(self, query: str, *, k: int = settings.top_k, source_filter: Optional[str] = None) -> List[Dict[str, str]]:
        where = {"source_type": source_filter} if source_filter else None
        return self.store.similarity_search(query, k=k, where=where)

    def build_context(self, docs: List[Dict[str, str]], *, max_chars: int = settings.max_context_chars) -> str:
        seen = set()
        context_parts: List[str] = []
        total = 0
        for doc in docs:
            snippet = doc.get("text", "")
            if snippet in seen:
                continue
            if total + len(snippet) > max_chars:
                break
            context_parts.append(snippet)
            seen.add(snippet)
            total += len(snippet)
        return "\n---\n".join(context_parts)

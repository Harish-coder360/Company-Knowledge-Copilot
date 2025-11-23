"""Vector store abstraction using ChromaDB."""
from __future__ import annotations

import os
import uuid
from typing import Dict, List, Optional, Sequence

import chromadb
from chromadb.config import Settings as ChromaSettings
from urllib.parse import urlparse

from app.core.config import settings


Metadata = Dict[str, str]


class VectorStore:
    """Wrapper around Chroma collections for similarity search."""

    def __init__(self, collection: str = "company-knowledge") -> None:
        if settings.vector_db_url:
            parsed = urlparse(settings.vector_db_url)
            client = chromadb.HttpClient(host=parsed.hostname or settings.vector_db_url, port=parsed.port or 8000, ssl=parsed.scheme == "https")
        else:
            persist_dir = settings.vector_db_path
            os.makedirs(persist_dir, exist_ok=True)
            client = chromadb.Client(
                ChromaSettings(
                    persist_directory=persist_dir,
                    chroma_api_impl="chromadb.api.local.LocalAPI",
                )
            )
        self.collection = client.get_or_create_collection(collection)

    def add_texts(
        self,
        texts: Sequence[str],
        metadatas: Sequence[Metadata],
        embeddings: Optional[Sequence[Sequence[float]]] = None,
    ) -> List[str]:
        """Insert documents with metadata and return generated ids."""

        ids = [str(uuid.uuid4()) for _ in texts]
        self.collection.add(
            documents=list(texts),
            metadatas=list(metadatas),
            embeddings=list(embeddings) if embeddings is not None else None,
            ids=ids,
        )
        return ids

    def similarity_search(
        self, query: str, k: int = 4, where: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """Return top-k documents with metadata and scores."""

        results = self.collection.query(query_texts=[query], n_results=k, where=where)
        docs: List[Dict[str, str]] = []
        for doc, meta, score in zip(
            results.get("documents", [[]])[0],
            results.get("metadatas", [[]])[0],
            results.get("distances", [[]])[0],
        ):
            docs.append({"text": doc, **(meta or {}), "score": score})
        return docs

    def list_sources(self) -> List[Dict[str, str]]:
        """Return metadata summary for indexed entries."""

        # Chroma does not expose counts per metadata key directly; this is a lightweight
        # approach for demo purposes.
        all_metadatas = self.collection.get(include=["metadatas"]).get("metadatas", [])
        summary: List[Dict[str, str]] = []
        for meta in all_metadatas:
            summary.append(meta or {})
        return summary

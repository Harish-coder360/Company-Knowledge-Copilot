"""Utilities that use MCP to bring GitHub content into the vector store."""
from __future__ import annotations

import logging
from typing import List

from app.core.config import settings
from app.mcp.client import MCPClient
from app.models.schemas import SourceMetadata
from app.rag.chunking import chunk_documents
from app.rag.embeddings import EmbeddingClient
from app.rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


def sync_github_repo(repo_url: str, store: VectorStore, embedder: EmbeddingClient) -> int:
    """Fetch docs from MCP GitHub server mirror and ingest into the vector DB."""

    client = MCPClient()
    assets = client.sync_github_repo(repo_url)
    if not assets:
        logger.warning("No MCP assets found for repo %s", repo_url)
        return 0

    chunks: List[str] = []
    metadatas: List[dict] = []
    for name, content in assets:
        doc_chunks = chunk_documents(
            [content], chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )
        chunks.extend(doc_chunks)
        metadatas.extend(
            [
                {
                    "source_type": "mcp-github",
                    "file_name": name,
                    "url": repo_url,
                    "content_type": "markdown",
                }
                for _ in doc_chunks
            ]
        )
    if not chunks:
        return 0
    embeddings = embedder.embed(chunks)
    store.add_texts(chunks, metadatas=metadatas, embeddings=embeddings)
    logger.info("Ingested %s chunks from MCP GitHub", len(chunks))
    return len(chunks)

"""Text chunking utilities."""
from __future__ import annotations

from typing import Iterable, List


def recursive_character_split(
    text: str,
    *,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[str]:
    """Split text into overlapping character chunks.

    A minimal RecursiveCharacterTextSplitter-style implementation that walks the
    text in windows and avoids empty segments.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    cleaned = text.strip()
    if not cleaned:
        return []

    chunks: List[str] = []
    start = 0
    step = chunk_size - chunk_overlap
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks


def chunk_documents(
    docs: Iterable[str], *, chunk_size: int = 1000, chunk_overlap: int = 200
) -> List[str]:
    """Chunk an iterable of documents into a flat list of segments."""

    all_chunks: List[str] = []
    for doc in docs:
        all_chunks.extend(
            recursive_character_split(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        )
    return all_chunks

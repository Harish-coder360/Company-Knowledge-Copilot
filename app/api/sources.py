"""Endpoints for listing indexed sources."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends

from app.models.schemas import SourceListItem
from app.rag.vectorstore import VectorStore

router = APIRouter(prefix="/api", tags=["sources"])


@router.get("/sources", response_model=List[SourceListItem])
async def list_sources(store: VectorStore = Depends(VectorStore)) -> List[SourceListItem]:
    metadatas = store.list_sources()
    items: List[SourceListItem] = []
    counter: Counter = Counter()
    created_lookup = {}
    for meta in metadatas:
        name = meta.get("file_name") or meta.get("url") or "unknown"
        key = (name, meta.get("source_type", "unknown"))
        counter[key] += 1
        created_lookup.setdefault(key, meta.get("created_at"))
    for (name, source_type), count in counter.items():
        created_raw = created_lookup.get((name, source_type))
        created = datetime.fromisoformat(created_raw) if created_raw else datetime.utcnow()
        items.append(
            SourceListItem(
                name=f"{name} ({count} chunks)",
                source_type=source_type,
                created_at=created,
            )
        )
    return items

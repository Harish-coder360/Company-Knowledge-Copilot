"""Endpoints for ingesting files and URLs."""
from __future__ import annotations

import io
import logging
import os
from datetime import datetime
from typing import List, Tuple

import httpx
from fastapi import APIRouter, File, UploadFile
from fastapi import HTTPException
from fastapi import Depends
from fastapi import BackgroundTasks
from bs4 import BeautifulSoup
from pypdf import PdfReader
import docx2txt

from app.core.config import settings
from app.models.schemas import IngestResponse, IngestURLRequest, SourceMetadata
from app.rag.chunking import chunk_documents
from app.rag.embeddings import EmbeddingClient
from app.rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ingest", tags=["ingest"])


def _parse_upload(file: UploadFile) -> Tuple[str, str]:
    """Extract text and detect content type from uploaded file."""

    filename = file.filename or "uploaded"
    ext = os.path.splitext(filename)[1].lower()
    content = file.file.read()
    if ext in {".txt", ".md"}:
        text = content.decode("utf-8", errors="ignore")
        content_type = "text"
    elif ext in {".pdf"}:
        pdf = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in pdf.pages]
        text = "\n".join(pages)
        content_type = "pdf"
    elif ext in {".docx"}:
        with io.BytesIO(content) as buf:
            text = docx2txt.process(buf)
        content_type = "docx"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    if not text.strip():
        raise HTTPException(status_code=400, detail="File contains no readable text")
    return text, content_type


def _chunk_and_store(
    texts: List[str],
    metadata: List[SourceMetadata],
    store: VectorStore,
    embedder: EmbeddingClient,
) -> int:
    all_chunks: List[str] = []
    metadatas: List[dict] = []
    for text, meta in zip(texts, metadata):
        doc_chunks = chunk_documents(
            [text], chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )
        if not doc_chunks:
            continue
        all_chunks.extend(doc_chunks)
        metadatas.extend(
            [
                {
                    "source_type": meta.source_type,
                    "file_name": meta.file_name,
                    "url": meta.url,
                    "content_type": meta.content_type,
                    "created_at": meta.created_at.isoformat(),
                }
                for _ in doc_chunks
            ]
        )
    if not all_chunks:
        return 0
    embeddings = embedder.embed(all_chunks)
    store.add_texts(all_chunks, metadatas=metadatas, embeddings=embeddings)
    return len(all_chunks)


@router.post("/files", response_model=IngestResponse)
async def ingest_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    store: VectorStore = Depends(VectorStore),
):
    embedder = EmbeddingClient()
    texts: List[str] = []
    metadatas: List[SourceMetadata] = []
    for file in files:
        text, content_type = _parse_upload(file)
        texts.append(text)
        metadatas.append(
            SourceMetadata(
                source_type="file",
                file_name=file.filename,
                content_type=content_type,
            )
        )

    def task() -> None:
        _chunk_and_store(texts, metadatas, store, embedder)

    background_tasks.add_task(task)
    return IngestResponse(inserted=len(texts), source_type="file")


async def _fetch_url(url: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.get_text("\n")


@router.post("/urls", response_model=IngestResponse)
async def ingest_urls(
    payload: IngestURLRequest,
    background_tasks: BackgroundTasks,
    store: VectorStore = Depends(VectorStore),
):
    embedder = EmbeddingClient()
    texts: List[str] = []
    metadatas: List[SourceMetadata] = []
    for url in payload.urls:
        content = await _fetch_url(url)
        texts.append(content)
        metadatas.append(
            SourceMetadata(
                source_type="url",
                url=url,
                content_type="html",
                created_at=datetime.utcnow(),
            )
        )

    def task() -> None:
        _chunk_and_store(texts, metadatas, store, embedder)

    background_tasks.add_task(task)
    return IngestResponse(inserted=len(texts), source_type="url")

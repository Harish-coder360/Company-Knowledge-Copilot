"""Chat endpoint implementing RAG over ingested data and MCP sources."""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI

from app.core.config import settings
from app.models.schemas import ChatRequest, ChatResponse, ChatResponseSource
from app.rag.embeddings import EmbeddingClient
from app.rag.retrieval import Retriever
from app.rag.vectorstore import VectorStore
from app.mcp.github_tools import sync_github_repo

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)


def _llm_generate(question: str, context: str) -> str:
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_api_base)
    system_prompt = (
        "You are Company Knowledge Copilot. Answer with only the provided context."
        " Cite sources inline using (Source N). If unsure, say you do not know."
    )
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}\nProvide a concise answer with citations."
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )
    return resp.choices[0].message.content or ""


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    store: VectorStore = Depends(VectorStore),
):
    retriever = Retriever(store)
    embedder = EmbeddingClient()

    if payload.enable_mcp:
        logger.info("Triggering MCP GitHub sync prior to retrieval")
        sync_github_repo("https://example.com/repo", store, embedder)

    top_k = payload.top_k or settings.top_k
    docs = retriever.fetch(payload.message, k=top_k, source_filter=payload.source_type)
    context = retriever.build_context(docs, max_chars=settings.max_context_chars)
    answer = _llm_generate(payload.message, context)

    sources: List[ChatResponseSource] = []
    for idx, doc in enumerate(docs, start=1):
        name = doc.get("file_name") or doc.get("url") or f"Source {idx}"
        snippet = doc.get("text", "")[:280]
        sources.append(
            ChatResponseSource(
                name=name,
                source_type=doc.get("source_type", "unknown"),
                snippet=snippet,
            )
        )

    return ChatResponse(answer=answer, sources=sources)

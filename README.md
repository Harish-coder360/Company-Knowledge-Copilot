# Company Knowledge Copilot

A production-style GenAI assistant that centralizes company knowledge using Retrieval Augmented Generation (RAG) plus Model Context Protocol (MCP) tooling. Upload documents, ingest URLs, or sync a GitHub mirror via MCP, then ask questions with grounded, cited responses.

## Overview & Problem Statement
Organizations struggle to keep policies, SOPs, and product docs discoverable. Fine-tuning quickly gets stale and is costly to update. This project demonstrates a generic, company-agnostic “Knowledge Copilot” that ingests docs/URLs, retrieves relevant context, and answers questions with citations. MCP adds tool access (e.g., GitHub repo mirror) so the assistant can stay fresh with live sources.

## Architecture
- **Flow:** Ingest → Chunk → Embed → Index → Retrieve → Generate.
- **RAG:**
  - Chunking via RecursiveCharacterTextSplitter-style logic (size/overlap configurable).
  - Embeddings through an OpenAI-compatible endpoint.
  - Vector DB: Chroma (embedded or HTTP service).
  - Retrieval: top-k similarity with optional source filters and max-context budget.
- **MCP Integration:**
  - `app/mcp/client.py` demonstrates connecting to an MCP mirror (treating `MCP_SERVER_CONFIG` as a synced folder).
  - `sync_github_repo` pulls README/docs-style markdown from the MCP mirror and feeds it into the ingest pipeline.
  - Chat can optionally trigger MCP sync before retrieval.
- **APIs (FastAPI):**
  - `POST /api/ingest/files` – upload PDF/DOCX/TXT/MD.
  - `POST /api/ingest/urls` – fetch and ingest URLs.
  - `POST /api/chat` – RAG-backed answers with citations; optional source filter & MCP sync.
  - `GET  /api/sources` – list indexed sources.
- **Frontend:** Next.js UI for uploads, URL ingest, chat, and source dashboard.

## Local Setup
1. Clone the repo and enter the directory.
2. Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` (and `MCP_SERVER_CONFIG` if using a local MCP mirror path).
3. Run `docker-compose up --build`.
4. Open the frontend at `http://localhost:3000` and API at `http://localhost:8000`.

## Running without Docker
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# In another terminal, from ./frontend
npm install
npm run dev
```

## Deployment
- **Backend (Docker) to Render/Railway:**
  - Create a new web service from this repo; point to `Dockerfile`; set env vars (`OPENAI_API_KEY`, `VECTOR_DB_URL` if using managed Chroma/Qdrant, `ALLOWED_ORIGINS`).
- **Frontend to Vercel:**
  - Import the `frontend` directory; set `NEXT_PUBLIC_API_BASE` to your backend URL.
- **Hugging Face Spaces (full stack):**
  - Use `docker-compose.yml` as the Space runtime; ensure `OPENAI_API_KEY` is set in Secrets.
## Project Structure
```
app/
  api/            # FastAPI routes (ingest, chat, sources)
  rag/            # Chunking, embeddings, vector store, retrieval
  mcp/            # MCP client + GitHub sync helper
  models/         # Pydantic schemas
  core/           # Config + logging
frontend/         # Next.js UI
tests/            # Pytest unit tests
```

## Sample Usage
1. Upload PDFs/DOCX via “Ingest sources” → “Upload & Embed”.
2. Paste docs/help-center URLs and ingest.
3. Toggle “Sync MCP GitHub” to pull from your MCP mirror folder, then ask questions.
4. View citations and snippets beside each answer.

## Notes
- Embeddings and chat rely on `OPENAI_API_KEY`/`OPENAI_API_BASE`; swap to any OpenAI-compatible provider.
- `MCP_SERVER_CONFIG` is treated as a local mirror path for simplicity; wire it to a live MCP GitHub server in production.
- Docker compose runs Chroma at `localhost:8001` (container port 8000); backend connects via internal service name.

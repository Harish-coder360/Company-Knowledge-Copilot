from fastapi.testclient import TestClient

from app.main import app
from app.api import chat as chat_module
from app.rag.vectorstore import VectorStore


class DummyStore:
    def similarity_search(self, query, k=4, where=None):
        return [
            {"text": "policy content", "source_type": "file", "file_name": "handbook.pdf"},
            {"text": "faq content", "source_type": "url", "url": "https://docs"},
        ][:k]


class DummyEmbedder:
    def __init__(self, *args, **kwargs):
        pass

    def embed(self, texts):
        return [[0.0 for _ in range(3)] for _ in texts]


def dummy_llm(question: str, context: str) -> str:
    return f"Answer for: {question}"


def dummy_sync(repo_url: str, store, embedder):
    return 0


def test_chat_endpoint(monkeypatch):
    monkeypatch.setattr(chat_module, "_llm_generate", dummy_llm)
    monkeypatch.setattr(chat_module, "EmbeddingClient", DummyEmbedder)
    monkeypatch.setattr(chat_module, "sync_github_repo", dummy_sync)

    app.dependency_overrides[VectorStore] = lambda: DummyStore()

    client = TestClient(app)
    response = client.post(
        "/api/chat",
        json={"message": "What is the policy?", "top_k": 2, "enable_mcp": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data["answer"].lower()
    assert len(data["sources"]) > 0

    app.dependency_overrides = {}

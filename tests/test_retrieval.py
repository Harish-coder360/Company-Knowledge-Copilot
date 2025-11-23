from typing import List, Dict

from app.rag.retrieval import Retriever


class DummyStore:
    def __init__(self, docs: List[Dict[str, str]]):
        self.docs = docs

    def similarity_search(self, query: str, k: int = 4, where=None):
        return self.docs[:k]


def test_build_context_dedupes_and_limits():
    doc_text = "snippet"
    docs = [
        {"text": doc_text, "source_type": "file"},
        {"text": doc_text, "source_type": "file"},
        {"text": "another", "source_type": "url"},
    ]
    retriever = Retriever(store=DummyStore(docs))
    ctx = retriever.build_context(docs, max_chars=15)
    assert ctx.count(doc_text) == 1
    assert "another" in ctx


def test_fetch_respects_k():
    docs = [{"text": str(i)} for i in range(10)]
    retriever = Retriever(store=DummyStore(docs))
    results = retriever.fetch("question", k=2)
    assert len(results) == 2

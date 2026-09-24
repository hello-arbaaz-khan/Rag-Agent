from typing import Protocol

from RagCore.Retrieval.bm25 import BM25Result
from RagCore.Retrieval.retrieval import RetrievalResult


class RetrievalRepository(Protocol):
    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[RetrievalResult]:
        ...


class LexicalRetriever(Protocol):
    def search(
        self,
        query: str,
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[BM25Result]:
        ...
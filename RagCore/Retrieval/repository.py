from typing import Protocol

from .retrieval import RetrievalResult


class RetrievalRepository(Protocol):
    def search(self,query_embedding: list[float],
    top_k: int,document_ids: list[str] | None = None,
    ) -> list[RetrievalResult]:
        ...
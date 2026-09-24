from collections import defaultdict

from RagCore.ErrorsHandle.exceptions import RetrievalError

from RagCore.Retrieval.bm25 import BM25Result
from RagCore.Retrieval.retrieval import RetrievalResult


class HybridRetriever:
    def __init__(
        self,
        vector_retriever,
        bm25_retriever,
        *,
        rrf_k: int = 60,
    ) -> None:
        if rrf_k <= 0:
            raise ValueError(
                "rrf_k must be greater than zero."
            )

        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        query_embedding: list[float],
        *,
        top_k: int = 20,
        candidate_k: int | None = None,
        document_ids: list[str] | None = None,
    ) -> list[RetrievalResult]:
        if not isinstance(query, str) or not query.strip():
            raise RetrievalError(
                "Query must be a non-empty string."
            )
    
        if top_k <= 0:
            raise RetrievalError(
                "top_k must be greater than zero."
            )
    
        if candidate_k is None:
            candidate_k = top_k
    
        if candidate_k <= 0:
            raise RetrievalError(
                "candidate_k must be greater than zero."
            )
    
        if document_ids is not None:
            if not isinstance(document_ids, list):
                raise RetrievalError(
                    "document_ids must be a list."
                )
    
            if any(
                not isinstance(document_id, str)
                or not document_id.strip()
                for document_id in document_ids
            ):
                raise RetrievalError(
                    "document_ids must contain non-empty string values."
                )
    
        vector_results = self.vector_retriever.retrieve(
            query_embedding,
            top_k=candidate_k,
            document_ids=document_ids,
        )
    
        bm25_results = self.bm25_retriever.search(
            query,
            top_k=candidate_k,
            document_ids=document_ids,
        )
    
        return self._fuse(
            vector_results,
            bm25_results,
            top_k=top_k,
        )

    def _fuse(
        self,
        vector_results: list[RetrievalResult],
        bm25_results: list[BM25Result],
        *,
        top_k: int,
    ) -> list[RetrievalResult]:
        fused_scores: defaultdict[str, float] = defaultdict(float)
        candidates: dict[str, RetrievalResult] = {}

        for rank, result in enumerate(
            vector_results,
            start=1,
        ):
            fused_scores[result.chunk_id] += (
                1.0 / (self.rrf_k + rank)
            )

            candidates[result.chunk_id] = result

        for rank, result in enumerate(
            bm25_results,
            start=1,
        ):
            fused_scores[result.chunk_id] += (
                1.0 / (self.rrf_k + rank)
            )

            if result.chunk_id not in candidates:
                candidates[result.chunk_id] = RetrievalResult(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    content=result.content,
                    score=result.score,
                    page_number=None,
                    chunk_index=0,
                    metadata={},
                )

        ranked_ids = sorted(
            candidates,
            key=lambda chunk_id: (
                -fused_scores[chunk_id],
                chunk_id,
            ),
        )

        results: list[RetrievalResult] = []

        for chunk_id in ranked_ids[:top_k]:
            result = candidates[chunk_id]

            metadata = dict(result.metadata)
            metadata["rrf_score"] = fused_scores[chunk_id]

            results.append(
                result.model_copy(
                    update={
                        "score": fused_scores[chunk_id],
                        "metadata": metadata,
                    }
                )
            )

        return results
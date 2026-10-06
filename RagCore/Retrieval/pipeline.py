from RagCore.ErrorsHandle.exceptions import RetrievalError

from RagCore.Retrieval.hybrid import HybridRetriever
from RagCore.Retrieval.repository import RetrievalRepository
from RagCore.Retrieval.retrieval import (
    RetrievalConfig,
    RetrievalMode,
    RetrievalResult,
    validate_query_embedding,
)


class RetrievalPipeline:
    def __init__(
        self,
        repository: RetrievalRepository,
        config: RetrievalConfig | None = None,
        hybrid_retriever: HybridRetriever | None = None,
    ) -> None:
        self.repository = repository
        self.config = config or RetrievalConfig()
        self.hybrid_retriever = hybrid_retriever

    def retrieve(
        self,
        query_embedding: list[float],
        *,
        query: str | None = None,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
    ) -> list[RetrievalResult]:

        requested_top_k = (
            self.config.top_k
            if top_k is None
            else top_k
        )

        if requested_top_k <= 0:
            raise RetrievalError(
                "top_k must be greater than zero."
            )

        if (
            document_ids is not None
            and any(
                not document_id
                for document_id in document_ids
            )
        ):
            raise RetrievalError(
                "document_ids must contain non-empty values."
            )

        try:
            validate_query_embedding(
                query_embedding,
                self.config.dimensions,
            )

            if self.config.mode == RetrievalMode.HYBRID:

                if self.hybrid_retriever is None:
                    raise RetrievalError(
                        "Hybrid retrieval is not configured."
                    )

                if (
                    not query
                    or not query.strip()
                ):
                    raise RetrievalError(
                        "Query is required for hybrid retrieval."
                    )

                results = self.hybrid_retriever.retrieve(
                    query=query.strip(),
                    query_embedding=query_embedding,
                    top_k=requested_top_k,
                    candidate_k=self.config.candidate_k,
                    document_ids=document_ids,
                )

            else:
                results = self.repository.search(
                    query_embedding,
                    requested_top_k,
                    document_ids,
                )

            if not isinstance(results, list):
                raise RetrievalError(
                    "Retrieval repository must return a list."
                )

            # Defensive deduplication.
            #
            # A chunk should never appear more than once in the
            # retrieval result.
            unique: dict[str, RetrievalResult] = {}

            for result in results:
                if not isinstance(
                    result,
                    RetrievalResult,
                ):
                    raise RetrievalError(
                        "Retrieval returned an invalid result."
                    )

                existing = unique.get(
                    result.chunk_id
                )

                if existing is None:
                    unique[
                        result.chunk_id
                    ] = result
                    continue

                if result.score > existing.score:
                    unique[
                        result.chunk_id
                    ] = result

            return list(
                unique.values()
            )[:requested_top_k]

        except RetrievalError:
            raise

        except Exception as exc:
            raise RetrievalError(
                str(exc)
            ) from exc
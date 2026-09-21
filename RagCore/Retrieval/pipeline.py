from RagCore.ErrorsHandle.exceptions import RetrievalError

from .repository import RetrievalRepository
from .retrieval import (
    RetrievalConfig,
    RetrievalResult,
    validate_query_embedding,
)


class RetrievalPipeline:
    def __init__(self,repository: RetrievalRepository,config: RetrievalConfig | None = None,
    ) -> None:

        self.repository = repository
        self.config = config or RetrievalConfig()

    def retrieve(self,query_embedding: list[float],*,top_k: int | None = None,document_ids: list[str] | None = None,
    ) -> list[RetrievalResult]:
    
        requested_top_k = (self.config.top_k if top_k is None else top_k)

        if requested_top_k <= 0:
            raise RetrievalError(
                "top_k must be greater than zero."
            )

        if (
            document_ids is not None
            and any(not document_id for document_id in document_ids)
        ):
            raise RetrievalError(
                "document_ids must contain non-empty values."
            )

        try:
            validate_query_embedding(
                query_embedding,
                self.config.dimensions,
            )

            return self.repository.search(
                query_embedding,
                requested_top_k,
                document_ids,
            )

        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(str(exc)) from exc
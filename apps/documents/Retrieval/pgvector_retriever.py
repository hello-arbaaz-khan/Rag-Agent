from pgvector.django import CosineDistance

from RagCore.ErrorsHandle.exceptions import RetrievalError

from RagCore.Retrieval.retrieval import RetrievalResult


class DjangoPgVectorRepository:
    def __init__(self, chunk_model) -> None:
        self.chunk_model = chunk_model

    def search(self,query_embedding: list[float],top_k: int,document_ids: list[str] | None = None,
    ) -> list[RetrievalResult]:

        try:
            queryset = self.chunk_model.objects.filter(
                embedding__isnull=False
            )

            if document_ids is not None:
                queryset = queryset.filter(
                    document_id__in=document_ids
                )

            rows = (queryset.annotate(distance=CosineDistance("embedding",query_embedding,))
            .order_by("distance")[:top_k]
            )

            return [self._to_result(row)
                for row in rows
            ]

        except Exception as exc:
            raise RetrievalError("Vector retrieval failed.")from exc

    @staticmethod
    def _to_result(row) -> RetrievalResult:
        content = getattr(row, "chunk_text", None)

        if content is None:
            content = getattr(row, "chunks_text", None)

        if content is None:
            raise RetrievalError(
                "Chunk model does not expose a supported content field."
            )

        chunk_index = getattr(row, "chunk_index", None)

        if chunk_index is None:
            chunk_index = getattr(row, "chunks_index", None)

        if chunk_index is None:
            raise RetrievalError(
                "Chunk model does not expose a supported chunk index field."
            )

        distance = getattr(row, "distance", None)

        if distance is None:
            raise RetrievalError(
                "Vector query did not return a distance."
            )

        return RetrievalResult(
            chunk_id=str(row.pk),
            document_id=str(row.document_id),
            content=content,
            score=1 - float(distance),
            page_number=getattr(row, "page_number", None),
            chunk_index=chunk_index,
        )
from __future__ import annotations

from collections.abc import Sequence

from django.db import transaction

from apps.documents.models import DocumemtsChunk, UploadedDocument
from RagCore.ErrorsHandle.exceptions import IntegrationError

class ChunkPersistenceService:
    """
    Persists RagCore chunks and embeddings into the existing
    Django DocumemtsChunk model.

    RagCore does not import Django. This class is the Django-side
    integration boundary.
    """

    EMBEDDING_DIMENSIONS = 384

    def persist(self,document: UploadedDocument,chunks: Sequence,embeddings: Sequence) -> int:
        if len(chunks) != len(embeddings):
            raise IntegrationError(
                "Number of chunks must match number of embeddings."
            )

        records = []

        for chunk, embedding_result in zip(
            chunks,
            embeddings,
            strict=True,
        ):
            vector = self._extract_embedding(embedding_result)

            if len(vector) != self.EMBEDDING_DIMENSIONS:
                raise IntegrationError(
                    f"Expected embedding dimension "
                    f"{self.EMBEDDING_DIMENSIONS}, "
                    f"got {len(vector)}."
                )

            records.append(
                DocumemtsChunk(
                    document=document,
                    chunks_text=self._get_chunk_text(chunk),
                    chunks_size=self._get_chunk_size(chunk),
                    chunks_index=self._get_chunk_index(chunk),
                    page_number=self._get_page_number(chunk),
                    embedding=vector,
                )
            )

        with transaction.atomic():
            # Reprocessing the same document must not leave old
            # chunks mixed with newly generated chunks.
            DocumemtsChunk.objects.filter(
                document=document
            ).delete()

            if records:
                DocumemtsChunk.objects.bulk_create(
                    records,
                    batch_size=500,
                )

            document.is_processed = True
            document.processing_error = None
            document.save(
                update_fields=[
                    "is_processed",
                    "processing_error",
                    "updated_at",
                ]
            )

        return len(records)

    @staticmethod
    def _extract_embedding(embedding_result) -> list[float]:
        """
        Supports the existing RagCore EmbeddingResult shape.
        """
        if hasattr(embedding_result, "embedding"):
            return list(embedding_result.embedding)

        if hasattr(embedding_result, "vector"):
            return list(embedding_result.vector)

        if isinstance(embedding_result, (list, tuple)):
            return list(embedding_result)

        raise IntegrationError(
            "Unsupported embedding result. "
            "Expected EmbeddingResult.embedding, "
            "EmbeddingResult.vector, or a sequence."
        )

    @staticmethod
    def _get_chunk_text(chunk) -> str:
        if hasattr(chunk, "text"):
            return chunk.text

        if hasattr(chunk, "content"):
            return chunk.content

        raise IntegrationError(
            "RagCore Chunk does not expose text/content."
        )

    @staticmethod
    def _get_chunk_size(chunk) -> int:
        if hasattr(chunk, "size"):
            return chunk.size

        text = ChunkPersistenceService._get_chunk_text(chunk)
        return len(text)

    @staticmethod
    def _get_chunk_index(chunk) -> int:
        if hasattr(chunk, "chunk_index"):
            return chunk.chunk_index

        if hasattr(chunk, "index"):
            return chunk.index

        raise IntegrationError(
            "RagCore Chunk does not expose chunk_index/index."
        )

    @staticmethod
    def _get_page_number(chunk):
        if hasattr(chunk, "page_number"):
            return chunk.page_number

        if hasattr(chunk, "page"):
            return chunk.page

        return None
from __future__ import annotations

from pathlib import Path

from django.db import transaction

from apps.documents.models import UploadedDocument

from RagCore.Chunking.pipeline import ChunkingPipeline
from RagCore.Embeddings.embedding import EmbeddingConfig
from RagCore.Embeddings.pipeline import EmbeddingPipeline
from RagCore.Embeddings.provider import SentenceTransformerProvider
from RagCore.Ingestion.pipeline import IngestionPipeline
from RagCore.ErrorsHandle.exceptions import IntegrationError

from Workflow.documents.chunk_persistence import (
    ChunkPersistenceService,
)


class DocumentProcessingWorkflow:
    """
    Application-level orchestration for document processing.

    Django owns persistence.
    RagCore owns AI/RAG processing.
    This workflow connects the two.
    """

    def __init__(
        self,
        ingestion_pipeline: IngestionPipeline | None = None,
        chunking_pipeline: ChunkingPipeline | None = None,
        embedding_pipeline: EmbeddingPipeline | None = None,
        persistence_service: ChunkPersistenceService | None = None,
    ):
        self.ingestion_pipeline = (
            ingestion_pipeline or IngestionPipeline()
        )

        self.chunking_pipeline = (
            chunking_pipeline or ChunkingPipeline()
        )

        if embedding_pipeline is None:
            embedding_config = EmbeddingConfig()

            embedding_provider = SentenceTransformerProvider(
                embedding_config
            )

            embedding_pipeline = EmbeddingPipeline(
                provid=embedding_provider,
                config=embedding_config,
            )

        self.embedding_pipeline = embedding_pipeline

        self.persistence_service = (
            persistence_service or ChunkPersistenceService()
        )

    def process(self, document_id: int) -> UploadedDocument:
        document = UploadedDocument.objects.get(
            pk=document_id
        )

        self._mark_processing(document)

        try:
            document_path = self._get_document_path(document)

            internal_document = self.ingestion_pipeline.run(
                file_path=document_path,
                document_id=str(document.pk),
            )

            chunks = self.chunking_pipeline.process(
                internal_document
            )

            embeddings = self.embedding_pipeline.process(
                chunks
            )

            self.persistence_service.persist(
                document=document,
                chunks=chunks,
                embeddings=embeddings,
            )

            document.refresh_from_db()

            return document

        except Exception as exc:
            self._mark_failed(document, exc)
            raise

    @staticmethod
    def _get_document_path(
        document: UploadedDocument,
    ) -> str:
        if not document.file:
            raise IntegrationError(
                f"Document {document.pk} has no uploaded file."
            )

        path = Path(document.file.path)

        if not path.exists():
            raise IntegrationError(
                f"Document file does not exist: {path}"
            )

        return str(path)

    @staticmethod
    def _mark_processing(
        document: UploadedDocument,
    ) -> None:
        document.is_processed = False
        document.processing_started_at = document.updated_at
        document.processing_error = None

        document.save(
            update_fields=[
                "is_processed",
                "processing_started_at",
                "processing_error",
                "updated_at",
            ]
        )

    @staticmethod
    def _mark_failed(
        document: UploadedDocument,
        exc: Exception,
    ) -> None:
        document.is_processed = False
        document.processing_error = str(exc)

        document.save(
            update_fields=[
                "is_processed",
                "processing_error",
                "updated_at",
            ]
        )
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.test import TestCase

from apps.documents.models import DocumemtsChunk, UploadedDocument

from RagCore.ErrorsHandle.exceptions import IntegrationError

from Workflow.documents.document_processing import (
    DocumentProcessingWorkflow,
)


User = get_user_model()


class DocumentProcessingWorkflowIntegrationTests(TestCase):
    """
    Real integration tests for the complete document-processing workflow.

    These tests intentionally do NOT mock RagCore components.

    Real pipeline:

        UploadedDocument
            ↓
        DocumentProcessingWorkflow
            ↓
        IngestionPipeline
            ↓
        ChunkingPipeline
            ↓
        EmbeddingPipeline
            ↓
        ChunkPersistenceService
            ↓
        Django PostgreSQL / pgvector
    """

    FIXTURES_DIR = (
        Path(__file__).resolve().parents[2]
        / "RagCore"
        / "Tests"
        / "Fixtures"
    )

    PDF_FIXTURE = (
        FIXTURES_DIR
        / "Pdf_samples"
        / "sample.pdf"
    )

    TWO_PAGE_PDF_FIXTURE = (
        FIXTURES_DIR
        / "Pdf_samples"
        / "sample_two_pages.pdf"
    )

    DOCX_FIXTURE = (
        FIXTURES_DIR
        / "Docx_samples"
        / "sample.docx"
    )

    def setUp(self):
        self.user = self._create_test_user()

        self.workflow = DocumentProcessingWorkflow()

    def _create_test_user(self):
        if User.USERNAME_FIELD == "email":
            return User.objects.create_user(
                email="workflow-real-test@example.com",
                password="test-password",
            )

        username_field = User._meta.get_field(
            User.USERNAME_FIELD
        )

        return User.objects.create_user(
            **{
                username_field.name: "workflow-real-test",
                "password": "test-password",
            }
        )

    def _create_document(
        self,
        fixture_path: Path,
        file_type: str,
    ) -> UploadedDocument:
        self.assertTrue(
            fixture_path.exists(),
            f"Real fixture does not exist: {fixture_path}",
        )

        with fixture_path.open("rb") as file_handle:
            django_file = File(
                file_handle,
                name=fixture_path.name,
            )

            document = UploadedDocument.objects.create(
                user=self.user,
                name=fixture_path.name,
                file=django_file,
                file_type=file_type,
                file_size=fixture_path.stat().st_size,
            )

        return document

    def _assert_successful_processing(
        self,
        document: UploadedDocument,
    ):
        document.refresh_from_db()

        self.assertTrue(
            document.is_processed,
            "Document should be marked as processed.",
        )

        self.assertIsNone(
            document.processing_error,
            "Successful processing must not contain an error.",
        )

        self.assertIsNotNone(
            document.processing_started_at,
            "Processing timestamp should be recorded.",
        )

        chunks = list(
            DocumemtsChunk.objects.filter(
                document=document
            ).order_by("chunks_index")
        )

        self.assertGreater(
            len(chunks),
            0,
            "Real document processing must create at least one chunk.",
        )

        return chunks

    def _assert_valid_chunks(
        self,
        chunks,
    ):
        for expected_index, chunk in enumerate(chunks):
            self.assertEqual(
                chunk.chunks_index,
                expected_index,
            )

            self.assertTrue(
                chunk.chunks_text,
                "Persisted chunk text must not be empty.",
            )

            self.assertIsNotNone(
                chunk.embedding,
                "Every persisted chunk must have an embedding.",
            )

            self.assertEqual(
                len(chunk.embedding),
                384,
                "Every embedding must contain exactly 384 dimensions.",
            )

    def test_real_pdf_is_processed_and_persisted(self):
        """
        Verifies the complete real PDF processing pipeline.
        """

        document = self._create_document(
            fixture_path=self.PDF_FIXTURE,
            file_type="pdf",
        )

        result = self.workflow.process(
            document.pk
        )

        self.assertEqual(
            result.pk,
            document.pk,
        )

        chunks = self._assert_successful_processing(
            document
        )

        self._assert_valid_chunks(
            chunks
        )

    def test_real_two_page_pdf_is_processed(self):
        """
        Verifies that a multi-page PDF is extracted, chunked,
        embedded, and persisted successfully.
        """

        document = self._create_document(
            fixture_path=self.TWO_PAGE_PDF_FIXTURE,
            file_type="pdf",
        )

        self.workflow.process(
            document.pk
        )

        chunks = self._assert_successful_processing(
            document
        )

        self._assert_valid_chunks(
            chunks
        )

        page_numbers = {
            chunk.page_number
            for chunk in chunks
            if chunk.page_number is not None
        }

        self.assertGreaterEqual(
            len(page_numbers),
            1,
        )

    def test_real_docx_is_processed_and_persisted(self):
        """
        Verifies the complete real DOCX processing pipeline.
        """

        document = self._create_document(
            fixture_path=self.DOCX_FIXTURE,
            file_type="docx",
        )

        result = self.workflow.process(
            document.pk
        )

        self.assertEqual(
            result.pk,
            document.pk,
        )

        chunks = self._assert_successful_processing(
            document
        )

        self._assert_valid_chunks(
            chunks
        )

    def test_real_processing_persists_correct_chunk_count(self):
        """
        Verifies that the number of persisted database chunks
        matches the number produced by the real processing pipeline.
        """

        document = self._create_document(
            fixture_path=self.PDF_FIXTURE,
            file_type="pdf",
        )

        self.workflow.process(
            document.pk
        )

        chunks = DocumemtsChunk.objects.filter(
            document=document
        )

        self.assertGreater(
            chunks.count(),
            0,
        )

        for chunk in chunks:
            self.assertIsNotNone(
                chunk.embedding
            )

    def test_real_reprocessing_replaces_existing_chunks(self):
        """
        Verifies that processing the same real document again
        does not leave stale chunks behind.
        """

        document = self._create_document(
            fixture_path=self.PDF_FIXTURE,
            file_type="pdf",
        )

        self.workflow.process(
            document.pk
        )

        first_chunks = list(
            DocumemtsChunk.objects.filter(
                document=document
            ).order_by("chunks_index")
        )

        self.assertGreater(
            len(first_chunks),
            0,
        )

        first_count = len(first_chunks)

        self.workflow.process(
            document.pk
        )

        second_chunks = list(
            DocumemtsChunk.objects.filter(
                document=document
            ).order_by("chunks_index")
        )

        self.assertGreater(
            len(second_chunks),
            0,
        )

        self.assertEqual(
            len(second_chunks),
            first_count,
        )

        self._assert_valid_chunks(
            second_chunks
        )

    def test_missing_real_file_fails_without_persisting_chunks(self):
        """
        Verifies the real workflow's missing-file error path.

        This test does not mock the pipeline. It creates a real
        UploadedDocument record and removes its physical file.
        """

        document = self._create_document(
            fixture_path=self.PDF_FIXTURE,
            file_type="pdf",
        )

        file_path = Path(
            document.file.path
        )

        self.assertTrue(
            file_path.exists()
        )

        file_path.unlink()

        with self.assertRaises(IntegrationError):
            self.workflow.process(
                document.pk
            )

        document.refresh_from_db()

        self.assertFalse(
            document.is_processed
        )

        self.assertTrue(
            document.processing_error
        )

        self.assertEqual(
            DocumemtsChunk.objects.filter(
                document=document
            ).count(),
            0,
        )

    def test_real_embeddings_are_384_dimensions(self):
        """
        Verifies that embeddings generated by the real
        SentenceTransformer provider are compatible with
        the database vector(384) column.
        """

        document = self._create_document(
            fixture_path=self.PDF_FIXTURE,
            file_type="pdf",
        )

        self.workflow.process(
            document.pk
        )

        chunks = DocumemtsChunk.objects.filter(
            document=document
        )

        self.assertGreater(
            chunks.count(),
            0,
        )

        for chunk in chunks:
            self.assertIsNotNone(
                chunk.embedding
            )

            self.assertEqual(
                len(chunk.embedding),
                384,
            )
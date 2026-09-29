from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.documents.models import DocumemtsChunk, UploadedDocument
from Workflow.documents.document_processing import DocumentProcessingWorkflow

User = get_user_model()

class DocumentProcessingWorkflowTests(TestCase):


    def setUp(self):
        self.user = self._create_test_user()
    
        self.uploaded_file_content = (
            b"Documind integration test document. "
            b"This document is used to verify the "
            b"Workflow to Django database connection."
        )
    
        self.document = UploadedDocument.objects.create(
            user=self.user,
            name="integration-test.txt",
            file=SimpleUploadedFile(
                "integration-test.txt",
                self.uploaded_file_content,
                content_type="text/plain",
            ),
            file_type="txt",
            file_size=len(self.uploaded_file_content),
        )
    
    def _create_test_user(self):
        """
        Create a user using the project's configured User model.
    
        Handles common Django custom-user configurations without
        assuming that the project uses a particular username field.
        """
        username_field = User._meta.get_field(
            User.USERNAME_FIELD
        )
    
        username = User.USERNAME_FIELD
    
        if username == "email":
            return User.objects.create_user(
                email="workflow-test@example.com",
                password="test-password",
            )
    
        return User.objects.create_user(
            **{
                username_field.name: "workflow-test",
                "password": "test-password",
            }
        )
    
    def _build_workflow(
        self,
        chunks=None,
        embeddings=None,
    ):
        """
        Build the workflow with controlled RagCore boundaries.
    
        This lets the test verify the real Django database
        persistence without depending on an external LLM/model
        during this integration test.
        """
        ingestion = Mock()
        chunking = Mock()
        embedding = Mock()
    
        ingestion.run.return_value = Mock(
            document_id=str(self.document.pk)
        )
    
        if chunks is None:
            chunks = self._build_chunks()
    
        if embeddings is None:
            embeddings = self._build_embeddings(
                len(chunks)
            )
    
        chunking.process.return_value = chunks
        embedding.process.return_value = embeddings
    
        workflow = DocumentProcessingWorkflow(
            ingestion_pipeline=ingestion,
            chunking_pipeline=chunking,
            embedding_pipeline=embedding,
        )
    
        return (
            workflow,
            ingestion,
            chunking,
            embedding,
        )
    
    @staticmethod
    def _build_chunks():
        chunk_1 = Mock()
        chunk_1.text = "First test chunk."
        chunk_1.size = len(chunk_1.text)
        chunk_1.chunk_index = 0
        chunk_1.page_number = 1
    
        chunk_2 = Mock()
        chunk_2.text = "Second test chunk."
        chunk_2.size = len(chunk_2.text)
        chunk_2.chunk_index = 1
        chunk_2.page_number = 1
    
        return [
            chunk_1,
            chunk_2,
        ]
    
    @staticmethod
    def _build_embeddings(count):
        return [
            Mock(embedding=[0.1] * 384)
            for _ in range(count)
        ]
    
    def test_successful_document_processing_persists_chunks(self):
        workflow, ingestion, chunking, embedding = (
            self._build_workflow()
        )
    
        result = workflow.process(
            self.document.pk
        )
    
        ingestion.run.assert_called_once()
        chunking.process.assert_called_once()
        embedding.process.assert_called_once()
    
        self.assertEqual(
            result.pk,
            self.document.pk,
        )
    
        self.assertEqual(
            DocumemtsChunk.objects.filter(
                document=self.document
            ).count(),
            2,
        )
    
        self.document.refresh_from_db()
    
        self.assertTrue(
            self.document.is_processed
        )
    
        self.assertIsNone(
            self.document.processing_error
        )
    
        chunks = list(
            DocumemtsChunk.objects.filter(
                document=self.document
            ).order_by("chunks_index")
        )
    
        self.assertEqual(
            chunks[0].chunks_text,
            "First test chunk.",
        )
    
        self.assertEqual(
            chunks[0].chunks_index,
            0,
        )
    
        self.assertEqual(
            chunks[0].page_number,
            1,
        )
    
        self.assertEqual(
            chunks[1].chunks_text,
            "Second test chunk.",
        )
    
        self.assertEqual(
            chunks[1].chunks_index,
            1,
        )
    
    def test_embeddings_are_persisted_with_384_dimensions(self):
        workflow, _, _, _ = self._build_workflow()
    
        workflow.process(
            self.document.pk
        )
    
        chunks = DocumemtsChunk.objects.filter(
            document=self.document
        )
    
        self.assertEqual(
            chunks.count(),
            2,
        )
    
        for chunk in chunks:
            self.assertIsNotNone(
                chunk.embedding
            )
    
            self.assertEqual(
                len(chunk.embedding),
                384,
            )
    
    def test_processing_marks_document_as_processed(self):
        workflow, _, _, _ = self._build_workflow()
    
        workflow.process(
            self.document.pk
        )
    
        self.document.refresh_from_db()
    
        self.assertTrue(
            self.document.is_processed
        )
    
        self.assertIsNone(
            self.document.processing_error
        )
    
        self.assertIsNotNone(
            self.document.processing_started_at
        )
    
    def test_processing_failure_marks_document_failed(self):
        ingestion = Mock()
        chunking = Mock()
        embedding = Mock()
    
        ingestion.run.side_effect = RuntimeError(
            "RagCore ingestion failed"
        )
    
        workflow = DocumentProcessingWorkflow(
            ingestion_pipeline=ingestion,
            chunking_pipeline=chunking,
            embedding_pipeline=embedding,
        )
    
        with self.assertRaises(RuntimeError):
            workflow.process(
                self.document.pk
            )
    
        self.document.refresh_from_db()
    
        self.assertFalse(
            self.document.is_processed
        )
    
        self.assertEqual(
            self.document.processing_error,
            "RagCore ingestion failed",
        )
    
        self.assertEqual(
            DocumemtsChunk.objects.filter(
                document=self.document
            ).count(),
            0,
        )
    
    def test_invalid_embedding_dimension_fails_processing(self):
        chunks = self._build_chunks()
    
        invalid_embeddings = [
            Mock(embedding=[0.1] * 383),
            Mock(embedding=[0.2] * 383),
        ]
    
        workflow, _, _, _ = self._build_workflow(
            chunks=chunks,
            embeddings=invalid_embeddings,
        )
    
        with self.assertRaises(ValueError):
            workflow.process(
                self.document.pk
            )
    
        self.document.refresh_from_db()
    
        self.assertFalse(
            self.document.is_processed
        )
    
        self.assertTrue(
            self.document.processing_error
        )
    
        self.assertEqual(
            DocumemtsChunk.objects.filter(
                document=self.document
            ).count(),
            0,
        )
    
    def test_reprocessing_replaces_existing_chunks(self):
        workflow, _, _, _ = self._build_workflow()
    
        workflow.process(
            self.document.pk
        )
    
        self.assertEqual(
            DocumemtsChunk.objects.filter(
                document=self.document
            ).count(),
            2,
        )
    
        new_chunk = Mock()
        new_chunk.text = "Reprocessed document chunk."
        new_chunk.size = len(new_chunk.text)
        new_chunk.chunk_index = 0
        new_chunk.page_number = 2
    
        new_embedding = Mock(
            embedding=[0.3] * 384
        )
    
        workflow, _, _, _ = self._build_workflow(
            chunks=[new_chunk],
            embeddings=[new_embedding],
        )
    
        workflow.process(
            self.document.pk
        )
    
        chunks = list(
            DocumemtsChunk.objects.filter(
                document=self.document
            ).order_by("chunks_index")
        )
    
        self.assertEqual(
            len(chunks),
            1,
        )
    
        self.assertEqual(
            chunks[0].chunks_text,
            "Reprocessed document chunk.",
        )
    
        self.assertEqual(
            chunks[0].page_number,
            2,
        )
    
    def test_chunk_and_embedding_counts_must_match(self):
        chunks = self._build_chunks()
    
        embeddings = [
            Mock(embedding=[0.1] * 384)
        ]
    
        workflow, _, _, _ = self._build_workflow(
            chunks=chunks,
            embeddings=embeddings,
        )
    
        with self.assertRaises(ValueError):
            workflow.process(
                self.document.pk
            )
    
        self.document.refresh_from_db()
    
        self.assertFalse(
            self.document.is_processed
        )
    
        self.assertEqual(
            DocumemtsChunk.objects.filter(
                document=self.document
            ).count(),
            0,
        )
from tempfile import TemporaryDirectory
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2] / "drive_service"),
)

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase, override_settings
from fastapi.testclient import TestClient

from apps.documents.models import DocumemtsChunk, UploadedDocument
from apps.documents.Retrieval.pgvector_retriever import (
    DjangoPgVectorRepository,
)
from apps.documents.services.search import DocumentSearchService
from drive_service.app.Apis.dependencies import get_current_user
from drive_service.app.Apis.routers.search import (
    get_document_search_service,
)
from drive_service.main import app
from RagCore.Embeddings.embedding import EmbeddingConfig
from RagCore.Embeddings.provider import SentenceTransformerProvider

User = get_user_model()


class DocumentSearchApiTests(TransactionTestCase):
    """Exercise the search API against PostgreSQL and real embeddings."""

    def setUp(self):
        self.temp_media = TemporaryDirectory()
        self.media_settings = override_settings(
            MEDIA_ROOT=self.temp_media.name,
        )
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)
        self.addCleanup(self.temp_media.cleanup)

        self.user = User.objects.create_user(
            email="search-test@example.com",
            password="test-password",
            display_name="Search Test User",
        )
        self.other_user = User.objects.create_user(
            email="other-search-test@example.com",
            password="test-password",
            display_name="Other Search Test User",
        )

        self.embedding_provider = SentenceTransformerProvider(
            EmbeddingConfig()
        )
        self.search_service = DocumentSearchService(
            embedding_provider=self.embedding_provider,
            vector_repository=DjangoPgVectorRepository(DocumemtsChunk),
        )

        self.previous_overrides = dict(app.dependency_overrides)
        app.dependency_overrides[get_current_user] = lambda: self.user.pk
        app.dependency_overrides[
            get_document_search_service
        ] = lambda: self.search_service
        self.addCleanup(self._restore_dependency_overrides)
        self.client = TestClient(app)

    def _restore_dependency_overrides(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.previous_overrides)

    def _create_processed_document(
        self,
        *,
        name,
        chunks,
        user=None,
        source=UploadedDocument.Source.UPLOAD,
    ):
        content = "\n".join(chunks).encode()
        document = UploadedDocument.objects.create(
            user=user or self.user,
            name=name,
            file=SimpleUploadedFile(name, content),
            file_type="pdf",
            source=source,
            file_size=len(content),
            is_processed=True,
        )
        embeddings = self.embedding_provider.embed(chunks)
        DocumemtsChunk.objects.bulk_create(
            [
                DocumemtsChunk(
                    document=document,
                    chunks_text=chunk_text,
                    chunks_size=len(chunk_text),
                    chunks_index=index,
                    embedding=embedding,
                )
                for index, (chunk_text, embedding) in enumerate(
                    zip(chunks, embeddings)
                )
            ]
        )
        return document

    def _search(self, query):
        response = self.client.get(
            "/api/v1/search",
            params={"query": query},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["results"]

    def test_semantic_content_search_combines_upload_and_drive_documents(self):
        upload_match = self._create_processed_document(
            name="Cricket.pdf",
            chunks=[
                "The political debate covered elections, public policy, and "
                "government institutions."
            ],
        )
        drive_match = self._create_processed_document(
            name="Meeting notes.pdf",
            source=UploadedDocument.Source.GOOGLE_DRIVE,
            chunks=[
                "This report discusses political information about voting "
                "rights and the national parliament."
            ],
        )
        misleading_name = self._create_processed_document(
            name="Pakistan.pdf",
            chunks=[
                "A recipe for vegetable soup with carrots, potatoes, and "
                "onions."
            ],
        )

        results = self._search("political information")
        result_ids = {result["id"] for result in results}

        self.assertIn(upload_match.pk, result_ids)
        self.assertIn(drive_match.pk, result_ids)
        self.assertNotIn(misleading_name.pk, result_ids)
        self.assertTrue(
            next(
                result
                for result in results
                if result["id"] == upload_match.pk
            )["matched_snippet"]
        )

    def test_content_queries_cover_war_cricket_and_programming_context(self):
        pakistan_war = self._create_processed_document(
            name="Regional history.pdf",
            chunks=[
                "The Pakistan war changed regional history and political "
                "relations across South Asia."
            ],
        )
        cricket = self._create_processed_document(
            name="Sports report.pdf",
            chunks=[
                "Cricket is played with a bat and ball by two teams on an "
                "oval field."
            ],
        )
        python = self._create_processed_document(
            name="Engineering notes.pdf",
            chunks=[
                "Django is a Python web framework used to build database "
                "backed applications."
            ],
        )

        expected = {
            "information about Pakistan war": pakistan_war.pk,
            "documents about cricket": cricket.pk,
            "give me documents that discuss Django and Python": python.pk,
        }
        for query, expected_id in expected.items():
            with self.subTest(query=query):
                results = self._search(query)
                self.assertIn(
                    expected_id,
                    {result["id"] for result in results},
                )

    def test_exact_filename_queries_prioritize_only_the_named_document(self):
        exact_match = self._create_processed_document(
            name="Pakistan War.pdf",
            chunks=["A gardening guide about soil and seasonal flowers."],
        )
        semantically_similar = self._create_processed_document(
            name="History.pdf",
            chunks=[
                "The Pakistan war influenced political history and "
                "international relations."
            ],
        )

        for query in (
            "find Pakistan War.pdf",
            "give me the document named Pakistan War.pdf",
        ):
            with self.subTest(query=query):
                results = self._search(query)
                self.assertEqual(
                    [result["id"] for result in results],
                    [exact_match.pk],
                )
                self.assertNotIn(
                    semantically_similar.pk,
                    {result["id"] for result in results},
                )
                self.assertEqual(
                    results[0]["relevance_score"],
                    1.0,
                )

    def test_multiple_matching_chunks_return_one_document_with_a_snippet(self):
        document = self._create_processed_document(
            name="Two-part report.pdf",
            chunks=[
                "The political campaign focused on democratic elections.",
                "Political information was shared by the national government.",
            ],
        )

        results = self._search("political information")
        matches = [
            result for result in results if result["id"] == document.pk
        ]

        self.assertEqual(len(matches), 1)
        self.assertTrue(matches[0]["matched_snippet"])

    def test_search_enforces_ownership_and_excludes_unprocessed_documents(self):
        owned_document = self._create_processed_document(
            name="Owned report.pdf",
            chunks=["Cricket is a popular sport played internationally."],
        )
        self._create_processed_document(
            name="Private report.pdf",
            user=self.other_user,
            chunks=["Cricket is a popular sport played internationally."],
        )
        unprocessed = UploadedDocument.objects.create(
            user=self.user,
            name="Pending cricket.pdf",
            file=SimpleUploadedFile("Pending cricket.pdf", b""),
            file_type="pdf",
            is_processed=False,
        )

        results = self._search("documents about cricket")
        result_ids = {result["id"] for result in results}

        self.assertIn(owned_document.pk, result_ids)
        self.assertNotIn(unprocessed.pk, result_ids)
        self.assertFalse(
            UploadedDocument.objects.filter(
                user=self.other_user,
                id__in=result_ids,
            ).exists()
        )

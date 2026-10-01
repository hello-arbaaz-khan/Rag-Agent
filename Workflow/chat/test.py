from pathlib import Path

from django.test import TestCase

from apps.auth_manager.models import User
from apps.chat.models import ChatHistory
from apps.documents.models import UploadedDocument, DocumemtsChunk

from Workflow.chat.processing import ChatQueryWorkflow
from Workflow.documents.document_processing import (
    DocumentProcessingWorkflow,
)


class ChatQueryIntegrationTests(TestCase):
    """
    Real Django -> Workflow -> RagCore chat integration tests.

    The document setup uses a real fixture and the real document
    processing workflow.

    No fake chunks or fake embeddings are created.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="chat-test@example.com",
            password="test-password",
            display_name="Chat Test User",
        )

        cls.document = cls._create_real_processed_document(
            cls.user,
        )

    @classmethod
    def _create_real_processed_document(cls, user):
        fixture = cls._get_real_fixture()

        with fixture.open("rb") as file:
            from django.core.files.uploadedfile import (
                SimpleUploadedFile,
            )

            uploaded_file = SimpleUploadedFile(
                fixture.name,
                file.read(),
                content_type=cls._content_type(
                    fixture.suffix.lower()
                ),
            )

        document = UploadedDocument.objects.create(
            user=user,
            name=fixture.name,
            file=uploaded_file,
            file_type=fixture.suffix.lower().lstrip("."),
            file_size=fixture.stat().st_size,
        )

        workflow = DocumentProcessingWorkflow()

        document = workflow.process(
            document.id,
        )

        document.refresh_from_db()

        if not document.is_processed:
            raise AssertionError(
                "Real document processing failed: "
                f"{document.processing_error}"
            )

        chunks = DocumemtsChunk.objects.filter(
            document=document,
        )

        if not chunks.exists():
            raise AssertionError(
                "Real document processing produced no chunks."
            )

        for chunk in chunks:
            if chunk.embedding is None:
                raise AssertionError(
                    "Real document chunk has no embedding."
                )

        return document

    @classmethod
    def _get_real_fixture(cls):
        fixtures_root = (
            Path(__file__).resolve().parents[2]
            / "RagCore"
            / "Tests"
            / "Fixtures"
        )

        pdf_dir = fixtures_root / "Pdf_samples"
        docx_dir = fixtures_root / "Docx_samples"

        candidates = []

        if pdf_dir.exists():
            candidates.extend(
                sorted(pdf_dir.glob("*.pdf"))
            )

        if docx_dir.exists():
            candidates.extend(
                sorted(docx_dir.glob("*.docx"))
            )

        if not candidates:
            raise AssertionError(
                "No real PDF or DOCX fixture was found under "
                f"{fixtures_root}"
            )

        return candidates[0]

    @staticmethod
    def _content_type(extension):
        return {
            ".pdf": "application/pdf",
            ".docx": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        }.get(
            extension,
            "application/octet-stream",
        )

    def test_real_document_chat_query(self):
        workflow = ChatQueryWorkflow(
            agent=self._build_real_agent(),
        )

        result = workflow.run(
            user=self.user,
            question="What is this document about?",
            document_id=self.document.id,
        )

        self.assertTrue(result.answer)

        self.assertEqual(
            result.document_id,
            self.document.id,
        )

        history = ChatHistory.objects.get(
            id=result.chat_history_id,
        )

        self.assertEqual(
            history.document_id,
            self.document.id,
        )

        self.assertEqual(
            history.question,
            "What is this document about?",
        )

        self.assertEqual(
            history.answer,
            result.answer,
        )

    def test_real_document_second_query_uses_history(self):
        workflow = ChatQueryWorkflow(
            agent=self._build_real_agent(),
        )

        first = workflow.run(
            user=self.user,
            question="What is this document about?",
            document_id=self.document.id,
        )

        second = workflow.run(
            user=self.user,
            question="Can you explain that in more detail?",
            document_id=self.document.id,
        )

        self.assertTrue(first.answer)
        self.assertTrue(second.answer)

        histories = ChatHistory.objects.filter(
            document=self.document,
        ).order_by("created_at", "id")

        self.assertEqual(
            histories.count(),
            2,
        )

        self.assertEqual(
            histories[0].question,
            "What is this document about?",
        )

        self.assertEqual(
            histories[1].question,
            "Can you explain that in more detail?",
        )

    def test_real_document_cannot_be_queried_by_another_user(self):
        other_user = User.objects.create_user(
            email="other-chat-test@example.com",
            password="test-password",
            display_name="Other User",
        )

        workflow = ChatQueryWorkflow(
            agent=self._build_real_agent(),
        )

        from RagCore.ErrorsHandle.exceptions import (
            IntegrationError,
        )

        with self.assertRaises(IntegrationError):
            workflow.run(
                user=other_user,
                question="Read this document.",
                document_id=self.document.id,
            )

        self.assertEqual(
            ChatHistory.objects.filter(
                document=self.document,
            ).count(),
            0,
        )

    @staticmethod
    def _build_real_agent():
        """
        Build the real RagCore Agent.

        This method connects the project's actual configured
        retrieval repository, embedding model, reranker, context builder,
        planner, and LLM generation provider.
        """
        from apps.documents.models import DocumemtsChunk
        from apps.documents.Retrieval.pgvector_retriever import (
            DjangoPgVectorRepository,
        )
        from RagCore.Agent.agent import Agent, AgentConfig
        from RagCore.Agent.executor import AgentExecutor
        from RagCore.Agent.planner import AgentPlanner
        from RagCore.Agent.tools import DocumentSearchTool
        from RagCore.Context.builder import ContextBuilder
        from RagCore.Embeddings.embedding import EmbeddingConfig
        from RagCore.Embeddings.provider import SentenceTransformerProvider
        from RagCore.Generation.generation import GenerationConfig
        from RagCore.Generation.pipeline import GenerationPipeline
        from RagCore.Generation.provider import GroqProvider
        from RagCore.Query.pipeline import QueryPipeline
        from RagCore.Reranking.pipeline import RerankingPipeline
        from RagCore.Reranking.provider import PassthroughRerankerProvider
        from RagCore.Reranking.reranking import RerankingConfig
        from RagCore.Retrieval.pipeline import RetrievalPipeline
        from RagCore.Retrieval.retrieval import RetrievalConfig

        embedding_config = EmbeddingConfig()
        embedding_provider = SentenceTransformerProvider(embedding_config)

        repository = DjangoPgVectorRepository(DocumemtsChunk)
        retrieval_config = RetrievalConfig(dimensions=384, top_k=20)
        retrieval_pipeline = RetrievalPipeline(
            repository=repository,
            config=retrieval_config,
        )

        reranker_provider = PassthroughRerankerProvider()
        reranking_pipeline = RerankingPipeline(
            provider=reranker_provider,
            config=RerankingConfig(top_k=5),
        )

        query_pipeline = QueryPipeline()

        search_tool = DocumentSearchTool(
            query_pipeline=query_pipeline,
            embedding_provider=embedding_provider,
            retrieval_pipeline=retrieval_pipeline,
            reranking_pipeline=reranking_pipeline,
        )

        executor = AgentExecutor(
            search_tool=search_tool,
            max_steps=5,
        )

        generation_config = GenerationConfig(model="openai/gpt-oss-20b")
        groq_provider = GroqProvider(config=generation_config)

        planner = AgentPlanner(
            provider=groq_provider,
            max_subqueries=5,
        )

        context_builder = ContextBuilder()

        generation_pipeline = GenerationPipeline(
            provider=groq_provider,
            config=generation_config,
        )

        return Agent(
            planner=planner,
            executor=executor,
            context_builder=context_builder,
            generation_pipeline=generation_pipeline,
            config=AgentConfig(
                retrieval_top_k=20,
                reranking_top_k=5,
                max_steps=5,
                max_subqueries=5,
            ),
        )
from pathlib import Path

from django.test import TestCase

from apps.auth_manager.models import User
from apps.chat.models import ChatMessage, Conversation, ConversationDocument
from apps.documents.models import UploadedDocument, DocumemtsChunk

from Workflow.chat.processing import ChatQueryWorkflow
from Workflow.documents.document_processing import DocumentProcessingWorkflow


class ChatQueryIntegrationTests(TestCase):
    """Real Django -> Workflow -> RagCore multi-document chat tests."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="chat-test@example.com",
            password="test-password",
            display_name="Chat Test User",
        )

        cls.document = cls._create_real_processed_document(cls.user, 0)
        cls.document_two = cls._create_real_processed_document(cls.user, 1)

    @classmethod
    def _create_real_processed_document(cls, user, fixture_index):
        fixture = cls._get_real_fixtures()[fixture_index]

        with fixture.open("rb") as file:
            from django.core.files.uploadedfile import SimpleUploadedFile

            uploaded_file = SimpleUploadedFile(
                fixture.name,
                file.read(),
                content_type=cls._content_type(fixture.suffix.lower()),
            )

        document = UploadedDocument.objects.create(
            user=user,
            name=fixture.name,
            file=uploaded_file,
            file_type=fixture.suffix.lower().lstrip("."),
            file_size=fixture.stat().st_size,
        )

        document = DocumentProcessingWorkflow().process(document.id)
        document.refresh_from_db()

        if not document.is_processed:
            raise AssertionError(
                "Real document processing failed: "
                f"{document.processing_error}"
            )

        chunks = DocumemtsChunk.objects.filter(document=document)
        if not chunks.exists():
            raise AssertionError("Real document processing produced no chunks.")

        for chunk in chunks:
            if chunk.embedding is None:
                raise AssertionError("Real document chunk has no embedding.")

        return document

    @classmethod
    def _get_real_fixtures(cls):
        fixtures_root = Path(__file__).resolve().parents[2] / "RagCore" / "Tests" / "Fixtures"
        candidates = sorted((fixtures_root / "Pdf_samples").glob("*.pdf")) if (fixtures_root / "Pdf_samples").exists() else []
        candidates += sorted((fixtures_root / "Docx_samples").glob("*.docx")) if (fixtures_root / "Docx_samples").exists() else []
        if len(candidates) < 2:
            raise AssertionError(f"At least two real PDF/DOCX fixtures are required under {fixtures_root}")
        return candidates

    @staticmethod
    def _content_type(extension):
        return {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }.get(extension, "application/octet-stream")

    @staticmethod
    def _create_conversation(user, documents):
        conversation = Conversation.objects.create(user=user, title="Multi-document test")
        ConversationDocument.objects.bulk_create([
            ConversationDocument(conversation=conversation, document=document)
            for document in documents
        ])
        return conversation

    def test_multi_document_chat_query(self):
        conversation = self._create_conversation(
            self.user,
            [self.document, self.document_two],
        )

        result = ChatQueryWorkflow(agent=self._build_real_agent()).run(
            user=self.user,
            question="What are these documents about?",
            conversation_id=conversation.id,
        )

        self.assertTrue(result.answer)
        self.assertEqual(result.conversation_id, conversation.id)
        self.assertEqual(
            ChatMessage.objects.filter(conversation=conversation).count(),
            2,
        )
        self.assertEqual(
            list(conversation.documents.order_by("id").values_list("id", flat=True)),
            [self.document.id, self.document_two.id],
        )

    def test_follow_up_uses_conversation_history(self):
        conversation = self._create_conversation(self.user, [self.document, self.document_two])
        workflow = ChatQueryWorkflow(agent=self._build_real_agent())

        first = workflow.run(
            user=self.user,
            question="What are these documents about?",
            conversation_id=conversation.id,
        )
        second = workflow.run(
            user=self.user,
            question="Can you explain that in more detail?",
            conversation_id=conversation.id,
        )

        self.assertTrue(first.answer)
        self.assertTrue(second.answer)
        self.assertEqual(ChatMessage.objects.filter(conversation=conversation).count(), 4)

    def test_user_cannot_query_another_users_conversation(self):
        conversation = self._create_conversation(self.user, [self.document, self.document_two])
        other_user = User.objects.create_user(
            email="other-chat-test@example.com",
            password="test-password",
            display_name="Other User",
        )

        from RagCore.ErrorsHandle.exceptions import IntegrationError

        with self.assertRaises(IntegrationError):
            ChatQueryWorkflow(agent=self._build_real_agent()).run(
                user=other_user,
                question="Read these documents.",
                conversation_id=conversation.id,
            )

        self.assertEqual(ChatMessage.objects.filter(conversation=conversation).count(), 0)

    @staticmethod
    def _build_real_agent():
        from apps.documents.models import DocumemtsChunk
        from apps.documents.Retrieval.pgvector_retriever import DjangoPgVectorRepository
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
        retrieval_pipeline = RetrievalPipeline(
            repository=repository,
            config=RetrievalConfig(dimensions=384, top_k=20),
        )
        reranking_pipeline = RerankingPipeline(
            provider=PassthroughRerankerProvider(),
            config=RerankingConfig(top_k=5),
        )
        search_tool = DocumentSearchTool(
            query_pipeline=QueryPipeline(),
            embedding_provider=embedding_provider,
            retrieval_pipeline=retrieval_pipeline,
            reranking_pipeline=reranking_pipeline,
        )
        executor = AgentExecutor(search_tool=search_tool, max_steps=5)
        generation_config = GenerationConfig(model="openai/gpt-oss-20b")
        groq_provider = GroqProvider(config=generation_config)
        planner = AgentPlanner(provider=groq_provider, max_subqueries=5)
        generation_pipeline = GenerationPipeline(provider=groq_provider, config=generation_config)

        return Agent(
            planner=planner,
            executor=executor,
            context_builder=ContextBuilder(),
            generation_pipeline=generation_pipeline,
            config=AgentConfig(
                retrieval_top_k=20,
                reranking_top_k=5,
                max_steps=5,
                max_subqueries=5,
            ),
        )
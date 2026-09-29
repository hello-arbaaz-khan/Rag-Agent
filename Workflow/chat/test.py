from pathlib import Path

from django.test import TestCase

from apps.auth_manager.models import User
from apps.chat.models import ChatHistory
from apps.documents.models import UploadedDocument

from Workflow.chat.processing import ChatQueryWorkflow
from RagCore.Agent.agent import Agent


class ChatQueryIntegrationTests(TestCase):
    """
    Real Django -> Workflow -> RagCore chat integration tests.

    No Agent mock.
    Uses a real processed document, real chunks, real embeddings,
    real retrieval/reranking/context/generation, and real ChatHistory.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="chat-test@example.com",
            password="test-password",
            display_name="Chat Test User",
        )

        cls.document = cls._create_real_processed_document()

    @classmethod
    def _create_real_processed_document(cls):
        """
        Reuse the same real-document setup used by the completed
        document workflow tests.

        Do not create fake chunk text here.
        The document must already have real chunks and embeddings.
        """
        raise NotImplementedError(
            "Connect this to the existing real document-processing "
            "fixture/setup from Workflow/documents/test.py."
        )

    def test_real_document_chat_query(self):
        agent = Agent()

        workflow = ChatQueryWorkflow(
            agent=agent,
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
        agent = Agent()

        workflow = ChatQueryWorkflow(
            agent=agent,
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

        self.assertEqual(
            ChatHistory.objects.filter(
                document=self.document,
            ).count(),
            2,
        )

    def test_real_document_cannot_be_queried_by_another_user(self):
        other_user = User.objects.create_user(
            email="other-chat-test@example.com",
            password="test-password",
            display_name="Other User",
        )

        workflow = ChatQueryWorkflow(
            agent=Agent(),
        )

        from Workflow.chat.processing import ChatQueryError

        with self.assertRaises(ChatQueryError):
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
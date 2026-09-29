from dataclasses import dataclass

from apps.chat.models import ChatHistory
from apps.documents.models import UploadedDocument
from RagCore.Agent.agent import Agent
from RagCore.ErrorsHandle.exceptions import IntegrationError


@dataclass(frozen=True)
class ChatQueryResult:
    question: str
    answer: str
    document_id: int
    document_name: str
    chat_history_id: int


class ChatQueryWorkflow:
    """
    Connects Django chat/document ownership with the RagCore Agent.

    Django is responsible for:
    - authenticated user
    - document ownership
    - ChatHistory persistence

    RagCore is responsible for:
    - query processing
    - embeddings
    - retrieval
    - reranking
    - context
    - generation
    """

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def run(
        self,
        *,
        user,
        question: str,
        document_id: int,
    ) -> ChatQueryResult:
        if not isinstance(question, str):
            raise IntegrationError("Question must be a string.")

        question = question.strip()

        if not question:
            raise IntegrationError("Question cannot be empty.")

        document = (
            UploadedDocument.objects
            .filter(
                id=document_id,
                user=user,
            )
            .first()
        )

        if document is None:
            raise IntegrationError(
                "Document not found or you do not have access to it."
            )

        if not document.is_processed:
            raise IntegrationError(
                "Document is not ready for querying."
            )

        conversation_context = self._build_conversation_context(
            document=document,
        )

        try:
            answer = self.agent.run(
                question,
                document_ids=[str(document.id)],
                conversation_context=conversation_context,
            )
        except IntegrationError as exc:
            raise IntegrationError(
                "Failed to generate an answer."
            ) from exc
        except Exception as exc:
            raise IntegrationError(
                "Failed to process chat query."
            ) from exc

        if not isinstance(answer, str) or not answer.strip():
            raise IntegrationError(
                "RagCore returned an empty answer."
            )

        answer = answer.strip()

        history = ChatHistory.objects.create(
            document=document,
            question=question,
            answer=answer,
        )

        return ChatQueryResult(
            question=question,
            answer=answer,
            document_id=document.id,
            document_name=document.name,
            chat_history_id=history.id,
        )

    @staticmethod
    def _build_conversation_context(
        *,
        document: UploadedDocument,
    ) -> str:
        history = (
            ChatHistory.objects
            .filter(document=document)
            .order_by("created_at", "id")
        )

        if not history.exists():
            return ""

        parts = []

        for item in history:
            parts.append(
                f"User: {item.question}\n"
                f"Assistant: {item.answer}"
            )

        return "\n\n".join(parts)
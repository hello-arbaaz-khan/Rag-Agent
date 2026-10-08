from dataclasses import dataclass

from apps.chat.models import ChatMessage, Conversation
from RagCore.Agent.agent import Agent
from RagCore.ErrorsHandle.exceptions import IntegrationError


@dataclass(frozen=True)
class ChatQueryResult:
    conversation_id: int
    question: str
    answer: str
    user_message_id: int
    assistant_message_id: int


class ChatQueryWorkflow:
    """Connect Django conversation state to the RagCore Agent."""

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    def run(self, *, user, question: str, conversation_id: int) -> ChatQueryResult:
        if not isinstance(question, str):
            raise IntegrationError("Question must be a string.")

        question = question.strip()
        if not question:
            raise IntegrationError("Question cannot be empty.")

        conversation = (
            Conversation.objects
            .filter(id=conversation_id, user=user)
            .prefetch_related("documents", "messages")
            .first()
        )
        if conversation is None:
            raise IntegrationError("Conversation not found or you do not have access to it.")

        documents = list(conversation.documents.filter(user=user).order_by("id"))
        if not documents:
            raise IntegrationError("Conversation has no documents attached.")

        not_ready = [document.name for document in documents if not document.is_processed]
        if not_ready:
            raise IntegrationError("Document(s) are not ready for querying: " + ", ".join(not_ready))

        conversation_context = self._build_conversation_context(conversation=conversation)

        try:
            answer = self.agent.run(
                question,
                document_ids=[str(document.id) for document in documents],
                conversation_context=conversation_context,
            )
        except IntegrationError as exc:
            raise IntegrationError("Failed to generate an answer.") from exc
        except Exception as exc:
            raise IntegrationError("Failed to process chat query.") from exc

        if not isinstance(answer, str) or not answer.strip():
            raise IntegrationError("RagCore returned an empty answer.")

        answer = answer.strip()
        user_message = ChatMessage.objects.create(
            conversation=conversation,
            role=ChatMessage.Role.USER,
            content=question,
        )
        assistant_message = ChatMessage.objects.create(
            conversation=conversation,
            role=ChatMessage.Role.ASSISTANT,
            content=answer,
        )

        return ChatQueryResult(
            conversation_id=conversation.id,
            question=question,
            answer=answer,
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
        )

    @staticmethod
    def _build_conversation_context(*, conversation: Conversation) -> str:
        messages = ChatMessage.objects.filter(conversation=conversation).order_by("created_at", "id")
        return "\n\n".join(
            f"{message.role.capitalize()}: {message.content}"
            for message in messages
        )
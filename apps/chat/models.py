from django.conf import settings
from django.db import models

from apps.documents.models import UploadedDocument


class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    title = models.CharField(max_length=255, default="New chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    documents = models.ManyToManyField(
        UploadedDocument,
        through="ConversationDocument",
        related_name="conversations",
    )

    class Meta:
        ordering = ["-updated_at", "-id"]

    def __str__(self):
        return f"{self.title} ({self.user_id})"


class ConversationDocument(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="document_links",
    )
    document = models.ForeignKey(
        UploadedDocument,
        on_delete=models.CASCADE,
        related_name="conversation_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("conversation", "document"),
                name="unique_conversation_document",
            ),
        ]
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"Conversation {self.conversation_id} -> Document {self.document_id}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role} message in conversation {self.conversation_id}"
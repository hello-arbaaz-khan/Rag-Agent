from django.db import models
from apps.documents.models import UploadedDocument
# Create your models here.

class ChatHistory(models.Model):
    document = models.ForeignKey(UploadedDocument, on_delete=models.CASCADE, related_name='chat_history', verbose_name='Document')
    question = models.TextField(verbose_name='Question')
    answer = models.TextField(verbose_name='Answer')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:
        verbose_name = "Chat history"
        verbose_name_plural = "Chat histories"
        ordering = ['created_at']

    def __str__(self):
        return f"Chat history for {self.document.name}"
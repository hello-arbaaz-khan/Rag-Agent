from django.db import models

# Create your models here.
class UploadedDocument(models.Model):
    """
    This model stores information about documents uploaded by users.
    """

    FILE_TYPES_CHOICES = [
        ("pdf", "PDF"),
        ("doc", "DOC"),
        ("docx", "DOCX"),
        ("txt", "TXT")
    ]

    name = models.CharField(max_length=255, verbose_name = "File name")
    file = models.FileField(upload_to="uploads/documents", verbose_name="Uploaded file")
    file_type = models.CharField(max_length=10, choices=FILE_TYPES_CHOICES, verbose_name="File type")
    file_size = models.BigIntegerField(default=0, verbose_name="File size")
    is_processed = models.BooleanField(default=False, verbose_name="Is processed")
    processing_started_at = models.DateTimeField(null=True, blank=True, verbose_name="Processing started at")
    processing_error = models.TextField(default="", null=True, blank=True, verbose_name="Error processing file")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name="Updated at")

    class Meta:
        verbose_name = "Uploaded document"
        verbose_name_plural = "Uploaded documents"
        ordering = ['-created_at']

    def __str__(self):

        return f"{self.name} ({self.file_type}) - {'✓' if self.is_processed else '⏳'}"
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def chunk_count(self):
        return self.chunks.count()


class DocumemtsChunks(models.Model):

    document = models.ForeignKey(UploadedDocument, on_delete=models.CASCADE, related_name="chunks", verbose_name="Document")
    chunk_text = models.TextField(verbose_name="Chunk text")
    chunk_size = models.IntegerField(default=0, verbose_name="Chunks size")
    chunk_index = models.IntegerField(verbose_name="Chunks index")
    embedding = models.JSONField(verbose_name="Embedding", null=True, blank=True)
    page_number = models.IntegerField(default=0, verbose_name="Page number")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    
    class Meta:
        verbose_name = "Document chunk"
        verbose_name_plural = "Document chunks"
        ordering = ['chunk_index']

    def __str__(self):
        return f"Docu {self.document.name} | Chunk_index {self.chunk_index} | Page {self.page_number}"


class ChatHistory(models.Model):
    """ This model is for storing chat history between user and the AI. """

    document = models.ForeignKey(UploadedDocument, on_delete=models.CASCADE, related_name='chat_history', verbose_name='Document')
    question = models.TextField(verbose_name='Question')
    answer = models.TextField(verbose_name='Answer')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:
        verbose_name = "Chat history"
        verbose_name_plural = "Chat histories"
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat history for {self.document.name}"
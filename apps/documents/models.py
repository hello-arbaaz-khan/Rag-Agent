from django.db import models
from django.conf import settings
from pgvector.django import VectorField
from RagCore.Ingestion.document import ALL_ALLOWED_EXTENSIONS


FILE_TYPE_CHOICES = [
    (extension.lstrip("."), extension.lstrip(".").upper())
    for extension in dict.fromkeys(ALL_ALLOWED_EXTENSIONS)
]

class UploadedDocument(models.Model):
    class Source(models.TextChoices):
        UPLOAD = "upload", "Manual upload"
        GOOGLE_DRIVE = "google_drive", "Google Drive"

    FILE_TYPES_CHOICES = FILE_TYPE_CHOICES
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=255, verbose_name="File name")
    file = models.FileField(upload_to="uploads/documents", verbose_name="Uploaded file")
    file_type = models.CharField(max_length=10, choices=FILE_TYPES_CHOICES, verbose_name="File type")
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.UPLOAD,
        db_index=True,
    )
    google_drive_file_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
    )
    file_size = models.BigIntegerField(default=0, verbose_name="File size")
    file_hash = models.CharField(max_length=64, db_index=True, null=True, blank=True, verbose_name="File hash")
    is_processed = models.BooleanField(default=False, verbose_name="Is processed")
    processing_started_at = models.DateTimeField(null=True, blank=True, verbose_name="Processing started at")
    processing_error = models.TextField(default="", null=True, blank=True, verbose_name="Error processing file")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "file_hash"),
                condition=models.Q(
                    source="upload",
                    file_hash__isnull=False,
                ),
                name="unique_user_upload_file_hash",
            ),
            models.UniqueConstraint(
                fields=("user", "google_drive_file_id"),
                condition=models.Q(google_drive_file_id__isnull=False),
                name="unique_user_google_drive_file",
            ),
        ]
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


class DocumemtsChunk(models.Model):
    document = models.ForeignKey(UploadedDocument, on_delete=models.CASCADE, related_name="chunks", verbose_name="Document")
    chunks_text = models.TextField(verbose_name="Chunk text")
    chunks_size = models.IntegerField(default=0, verbose_name="Chunks size")
    chunks_index = models.IntegerField(verbose_name="Chunks index")
    embedding = VectorField(dimensions=384, verbose_name="Embedding", null=True, blank=True)
    page_number = models.IntegerField(default=0, verbose_name="Page number")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    class Meta:
        verbose_name = "Document chunk"
        verbose_name_plural = "Document chunks"
        ordering = ['id']

    def __str__(self):
        return f"Docu {self.document.name} | Chunk_index {self.chunk_index} | Page {self.page_number}"

from django.db import models
from django.conf import settings
# Create your models here.

class DriveDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="drive_documents")
    drive_file_id = models.CharField(max_length=255)
    name = models.CharField(max_length=500)
    mime_type = models.CharField(max_length=100)
    drive_modified_at = models.DateTimeField()

    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('indexed', 'Indexed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    sync_error = models.TextField(blank=True, null=True)

    document = models.OneToOneField(
        'documents.UploadedDocument',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drive_source'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "drive_file_id")

    def __str__(self):
        return f"{self.name} ({self.sync_status})"
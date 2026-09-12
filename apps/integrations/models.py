from django.db import models
from django.db.models.functions import Now
from django.conf import settings

# Create your models here.

class GoogleDriveAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="google_drive_account",
        verbose_name="User",
    )
    google_email = models.CharField(max_length=255, verbose_name="Google account email")
    google_account_id = models.CharField(max_length=255, verbose_name="Google account ID (sub)")

    access_token_encrypted = models.TextField(verbose_name="Encrypted access token")
    refresh_token_encrypted = models.TextField(verbose_name="Encrypted refresh token")
    token_expiry = models.DateTimeField(verbose_name="Access token expiry")
    scopes = models.TextField(verbose_name="Granted scopes")

    key_version = models.IntegerField(default=1, verbose_name="Encryption key version")

    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        db_table = "google_drive_accounts"
        verbose_name = "Google Drive account"
        verbose_name_plural = "Google Drive accounts"

    def __str__(self):
        return f"{self.user} → {self.google_email}"
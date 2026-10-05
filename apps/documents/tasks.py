from __future__ import annotations

from celery import shared_task

from Workflow.documents.document_processing import (
    DocumentProcessingWorkflow,
)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_document_task(
    self,
    document_id: int,
) -> None:
    """
    Process an uploaded document in the background.

    Celery owns the background-job execution.
    Workflow owns the document-processing orchestration.
    """

    workflow = DocumentProcessingWorkflow()

    workflow.process(
        document_id=document_id,
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def sync_google_drive_task(
    self,
    user_id: int,
) -> dict:
    """Synchronize one user's Drive into UploadedDocument records."""
    import os

    from django.conf import settings as django_settings
    from sqlalchemy.engine import URL

    database = django_settings.DATABASES["default"]
    os.environ["DATABASE_URL"] = URL.create(
        "postgresql",
        username=database["USER"],
        password=database["PASSWORD"],
        host=database["HOST"],
        port=int(database["PORT"]) if database["PORT"] else None,
        database=database["NAME"],
    ).render_as_string(hide_password=False)
    os.environ["REDIS_URL"] = django_settings.CELERY_BROKER_URL

    from drive_service.app.services.drive_sync import sync_google_drive

    return sync_google_drive(user_id)
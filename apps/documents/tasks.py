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

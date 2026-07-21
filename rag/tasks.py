from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from rag.utils.pdf_processor import process_document
from rag.models import UploadedDocument

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_document_task(self, document_id):
    try:
        document = UploadedDocument.objects.get(id=document_id)
        document.processing_started_at = timezone.now()
        document.save()
        process_document(document)
    except UploadedDocument.DoesNotExist:
        raise
    except Exception as e:
        try:
            document = UploadedDocument.objects.get(id=document_id)
            document.processing_error = repr(e)
            document.save()
        except Exception:
            pass
        raise self.retry(exc=e)

def requeue_stuck_documents():
    ten_minutes_ago = timezone.now() - timedelta(minutes=10)
    stuck_docs = UploadedDocument.objects.filter(
        is_processed=False,
        processing_started_at__isnull=False,
        processing_started_at__lt=ten_minutes_ago
    ).filter(Q(processing_error__isnull=True) | Q(processing_error=''))

    for doc in stuck_docs:
        process_document_task.delay(doc.id)

    return stuck_docs

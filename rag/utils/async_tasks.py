import threading
from rag.utils.pdf_processor import process_document
from rag.models import UploadedDocument
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

# Cap concurrent document processing to avoid overwhelming SQLite and the embedding model.
# With the embedding lock already serializing .encode() calls, having >3 threads
# provides no speedup and just wastes OS thread handles and memory.
# Tune this value up if you move to PostgreSQL and a GPU-accelerated embedding model.
_PROCESSING_SEMAPHORE = threading.Semaphore(3)


def process_document_async(document_id):
    """Process document in background thread to avoid blocking HTTP response."""
    def _process():
        import django.db
        django.db.close_old_connections()
        with _PROCESSING_SEMAPHORE:  # cap concurrent processing threads
            try:
                document = UploadedDocument.objects.get(id=document_id)
                document.processing_started_at = timezone.now()
                document.save()
                process_document(document)
            except Exception as e:
                print(f"Error processing document {document_id}: {repr(e)}", flush=True)
                try:
                    document = UploadedDocument.objects.get(id=document_id)
                    document.processing_error = repr(e)
                    document.save()
                except Exception:
                    pass
            finally:
                django.db.close_old_connections()

    thread = threading.Thread(target=_process, daemon=True)
    thread.start()


def requeue_stuck_documents():
    """Finds documents stuck in processing for more than 10 minutes and retries processing them."""
    ten_minutes_ago = timezone.now() - timedelta(minutes=10)
    stuck_docs = UploadedDocument.objects.filter(
        is_processed=False,
        processing_started_at__isnull=False,
        processing_started_at__lt=ten_minutes_ago
    ).filter(Q(processing_error__isnull=True) | Q(processing_error=''))

    for doc in stuck_docs:
        process_document_async(doc.id)

    return stuck_docs


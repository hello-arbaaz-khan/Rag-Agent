from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from apps.rag.models import UploadedDocument, DocumemtsChunks
from apps.rag.utils.pdf_processor import process_document


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_document_task(self, document_id):
    try:
        with transaction.atomic():
            document = UploadedDocument.objects.select_for_update(nowait=False).get(id=document_id)

            if document.is_processed:
                return {"status": "already_processed", "document_id": document_id}

            document.processing_started_at = timezone.now()
            document.save()

    except ObjectDoesNotExist:
        logger = __import__('logging').getLogger(__name__)
        logger.warning("Document %s not found at task start. Skipping.", document_id)
        return {"status": "document_not_found", "document_id": document_id}

    except Exception as e:
        raise self.retry(exc=e)

    try:
        process_document(document)

        with transaction.atomic():
            doc_check = UploadedDocument.objects.filter(id=document_id).first()
            if doc_check:
                doc_check.is_processed = True
                doc_check.processing_error = ""
                doc_check.save()
                return {"status": "success", "document_id": document_id}
            else:
                DocumemtsChunks.objects.filter(document_id=document_id).delete()
                return {"status": "deleted_during_processing", "document_id": document_id}

    except Exception as e:
        try:
            doc = UploadedDocument.objects.filter(id=document_id).first()
            if doc:
                doc.processing_error = repr(e)
                doc.save()
        except Exception:
            pass

        raise self.retry(exc=e)
import hashlib
import logging

from django.db import transaction
from apps.rag.models import UploadedDocument, DocumemtsChunks
from apps.rag.utils.vector_store import delete_document_collection
from apps.rag.tasks import process_document_task

logger = logging.getLogger(__name__)


class DocumentService:
    """Business logic for document upload, processing, and deletion."""

    @staticmethod
    def _generate_file_hash(file):
        file.seek(0)
        hasher = hashlib.md5()
        for chunk in file.chunks():
            hasher.update(chunk)
        file_hash = hasher.hexdigest()
        file.seek(0)
        return file_hash

    @staticmethod
    def create_and_process(file, name, file_type):
        file_hash = DocumentService._generate_file_hash(file)

        existing = UploadedDocument.objects.filter(file_hash=file_hash).first()
        if existing:
            return existing

        document = UploadedDocument.objects.create(
            name=name,
            file=file,
            file_type=file_type,
            file_size=file.size,
            file_hash=file_hash,
        )

        process_document_task.delay(document.id)
        return document

    @staticmethod
    def delete(document_id):
        with transaction.atomic():
            document = UploadedDocument.objects.select_for_update().get(id=document_id)

            DocumemtsChunks.objects.filter(document=document).delete()
            document.delete()

        try:
            delete_document_collection(document_id)
        except Exception as e:
            logger.error("Failed to delete vector chunks for doc %s: %s", document_id, e)

        return document

    @staticmethod
    def list_all():
        return UploadedDocument.objects.all().order_by("-created_at")

    @staticmethod
    def get_status(document_id):
        document = UploadedDocument.objects.get(id=document_id)
        return {
            "id": document.id,
            "name": document.name,
            "is_processed": document.is_processed,
            "processing_error": document.processing_error,
            "chunk_count": document.chunk_count,
        }
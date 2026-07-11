from rag.models import UploadedDocument
from rag.utils.vector_store import delete_document_collection
from rag.utils.async_tasks import process_document_async


class DocumentService:
    """Business logic for document upload, processing, and deletion."""

    @staticmethod
    def create_and_process(file, name, file_type):
        document = UploadedDocument.objects.create(
            name=name,
            file=file,
            file_type=file_type,
            file_size=file.size,
        )

        # Process document in background thread (non-blocking)
        process_document_async(document.id)

        return document

    @staticmethod
    def delete(document_id):
        import logging
        from django.db import transaction
        logger = logging.getLogger(__name__)

        document = UploadedDocument.objects.get(id=document_id)
        collection_name = f"document{document_id}"

        with transaction.atomic():
            document.delete()
            try:
                delete_document_collection(document_id)
            except Exception as e:
                logger.error("Failed to delete Chroma collection %s: %s. Collection is orphaned.", collection_name, e)
                print(f"Failed to delete Chroma collection {collection_name}: {e}. Collection is orphaned.")
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
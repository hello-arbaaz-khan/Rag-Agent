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
        document = UploadedDocument.objects.get(id=document_id)
        delete_document_collection(document_id)
        document.delete()
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
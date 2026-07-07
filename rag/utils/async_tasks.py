import threading
from rag.utils.pdf_processor import process_document
from rag.models import UploadedDocument


def process_document_async(document_id):
    """Process document in background thread to avoid blocking HTTP response."""
    def _process():
        try:
            document = UploadedDocument.objects.get(id=document_id)
            process_document(document)
        except Exception as e:
            print(f"Error processing document {document_id}: {str(e)}")
            try:
                document = UploadedDocument.objects.get(id=document_id)
                document.processing_error = str(e)
                document.save()
            except:
                pass
    
    thread = threading.Thread(target=_process, daemon=True)
    thread.start()

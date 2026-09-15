# rag_core/ingestion/pipeline.py
import os
from RagCore.Ingestion.document import (
    DOCUMENT_LAYOUT_FORMATS, 
    DOCUMENT_TEXT_FORMATS, 
    CHAT_VISION_FORMATS,
    InternalDocument,
    DocumentPage,
)
from RagCore.Ingestion.document_extraction import DocumentExtractionEngine
from RagCore.Ingestion.vision_extraction import VisionExtractionEngine 
from RagCore.Ingestion.exceptions import IngestionError

class IngestionPipeline:

    def run(self, file_path: str, document_id: str) -> InternalDocument:
            if not os.path.exists(file_path):
                raise IngestionError(f"File not found: {file_path}")
    
            _, ext = os.path.splitext(file_path.lower())
    
            pages: list[DocumentPage] = []
            engine_name = "Unknown Engine"
    
            # Route A: It is a normal document file (.pdf, .docx, .txt, etc.)
            if ext in DOCUMENT_LAYOUT_FORMATS or ext in DOCUMENT_TEXT_FORMATS:
                engine_name = "PyMuPDF / Core Extraction"
                try:
                    pages = DocumentExtractionEngine.extract_to_markdown(file_path)
                except Exception as err:
                    if "came up empty" in str(err) and ext == ".pdf":
                        # Vision OCR has no page concept of its own here -- the
                        # whole scanned PDF is sent as one image, so we treat
                        # the result as a single page (page_number=1).
                        vision_text = VisionExtractionEngine.extract_image_text(file_path)
                        pages = [DocumentPage(page_number=1, content=vision_text)]
                        engine_name = "Groq Vision Fallback (Scanned PDF OCR)"
                    else:
                        raise IngestionError(f"Document extraction crash: {str(err)}") from err
    
            # Route B: It is a direct image file (.png, .jpg, .webp)
            elif ext in CHAT_VISION_FORMATS:
                vision_text = VisionExtractionEngine.extract_image_text(file_path)
                pages = [DocumentPage(page_number=1, content=vision_text)]
                engine_name = "Groq Vision Engine"
    
            else:
                raise IngestionError(f"The file extension '{ext}' is completely unsupported.")
    
            if not pages or not any(page.content.strip() for page in pages):
                raise IngestionError(
                    "The file was processed successfully but contains absolutely no readable content."
                )
                    
            return InternalDocument(
                document_id=str(document_id),
                pages=pages,
                metadata={
                    "file_name": os.path.basename(file_path),
                    "extraction_engine": engine_name,
                    "page_count": len(pages),
                }
            )
# rag_core/ingestion/pipeline.py
import os
from RagCore.Ingestion.document import (
    DOCUMENT_LAYOUT_FORMATS, 
    DOCUMENT_TEXT_FORMATS, 
    CHAT_VISION_FORMATS,
    InternalDocument
)
from RagCore.Ingestion.document_extraction import DocumentExtractionEngine
from RagCore.Ingestion.vision_extraction import VisionExtractionEngine 
from RagCore.Ingestion.exceptions import IngestionError
from numpy.strings import strip
from pymupdf.table import extract_text

class IngestionPipeline:

    def run(self, file_path: str, document_id: str) -> InternalDocument:
            if not os.path.exists(file_path):
                raise IngestionError(f"File not found: {file_path}")
    
            _, ext = os.path.splitext(file_path.lower())
    
            extracted_text = ""
            engine_name = "Unknown Engine"
    
            # Route A: It is a normal document file (.pdf, .docx, .txt, etc.)
            if ext in DOCUMENT_LAYOUT_FORMATS or ext in DOCUMENT_TEXT_FORMATS:
                engine_name = "PyMuPDF / Core Extraction"
                try:
                    extracted_text = DocumentExtractionEngine.extract_to_markdown(file_path)
                except Exception as err:
                    if "came up empty" in str(err) and ext == ".pdf":
                        extracted_text = VisionExtractionEngine.extract_image_text(file_path)
                        engine_name = "Groq Vision Fallback (Scanned PDF OCR)"
                    else:
                        raise IngestionError(f"Document extraction crash: {str(err)}") from err
    
            # Route B: It is a direct image file (.png, .jpg, .webp)
            elif ext in CHAT_VISION_FORMATS:
                extracted_text = VisionExtractionEngine.extract_image_text(file_path)
                engine_name = "Groq Vision Engine"
    
            else:
                raise IngestionError(f"The file extension '{ext}' is completely unsupported.")
    
            if not extracted_text or not extracted_text.strip():
                raise IngestionError(
                    "The file was processed successfully but contains absolutely no readable content."
                )
                    
            return InternalDocument(
                document_id=str(document_id),
                content=extracted_text,
                metadata={
                    "file_name": os.path.basename(file_path),
                    "extraction_engine": engine_name
                }
            )
import os
import fitz

from RagCore.Ingestion.document import (
    DOCUMENT_LAYOUT_FORMATS,
    DOCUMENT_TEXT_FORMATS,
    CHAT_VISION_FORMATS,
    InternalDocument,
    DocumentPage,
)
from RagCore.Ingestion.document_extraction import DocumentExtractionEngine
from RagCore.Ingestion.vision_extraction import VisionExtractionEngine
from RagCore.Ingestion.exceptions import EmptyExtractionError, IngestionError


class IngestionPipeline:

    def run(self, file_path: str, document_id: str) -> InternalDocument:

        if not os.path.exists(file_path):
            raise IngestionError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path.lower())

        pages: list[DocumentPage] = []
        engine_name = "Unknown Engine"

        if ext in DOCUMENT_LAYOUT_FORMATS or ext in DOCUMENT_TEXT_FORMATS:
            engine_name = "PyMuPDF / Core Extraction"

            try:
                pages = DocumentExtractionEngine.extract_to_markdown(file_path)

            except EmptyExtractionError:
                if ext == ".pdf":
                    pages = VisionExtractionEngine.extract_pdf_pages(file_path)
                    engine_name = "Groq Vision Fallback (Scanned PDF OCR)"
                else:
                    raise
            except IngestionError as err:
                raise IngestionError(f"Document extraction failed: {err}") from err
            except Exception as err:
                raise IngestionError(f"Document extraction failed: {err}") from err

        elif ext in CHAT_VISION_FORMATS:
            pages = [
                DocumentPage(
                    page_number=1,
                    content=VisionExtractionEngine.extract_image_text(file_path),
                )
            ]
            engine_name = "Groq Vision Engine"

        else:
            raise IngestionError(f"The file extension '{ext}' is completely unsupported.")

        if not pages or not any(page.content.strip() for page in pages):
            raise IngestionError(
                "The file was processed successfully but contains absolutely no readable content."
            )

        page_count = len(pages)
        if ext == ".pdf" and engine_name == "Groq Vision Fallback (Scanned PDF OCR)":
            with fitz.open(file_path) as document:
                page_count = document.page_count

        return InternalDocument(
            document_id=str(document_id),
            pages=pages,
            metadata={
                "file_name": os.path.basename(file_path),
                "extraction_engine": engine_name,
                "page_count": page_count,
            },
        )
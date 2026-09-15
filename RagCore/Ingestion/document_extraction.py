import os
import fitz  # PyMuPDF
import pymupdf4llm
from RagCore.Ingestion.exceptions import IngestionError

from RagCore.Ingestion.document import (
    DOCUMENT_LAYOUT_FORMATS, 
    DOCUMENT_TEXT_FORMATS,
    ALL_ALLOWED_EXTENSIONS
)

class DocumentExtractionEngine:

    @classmethod
    def extract_to_markdown(cls, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise IngestionError(f"Target document file not found at: {file_path}")

        _, ext = os.path.splitext(file_path.lower())

        # 1. Global Guardrail
        if ext not in ALL_ALLOWED_EXTENSIONS:
            raise IngestionError(f"File extension '{ext}' is not supported by this system.")

        try:
            # 2. Handle Complex Layout Formats (.pdf, .epub, .html, etc.) via PyMuPDF4LLM
            if ext in DOCUMENT_LAYOUT_FORMATS:
                # Force casting to 'str' to completely satisfy strict Pyright/Pylance type engine
                markdown_data = pymupdf4llm.to_markdown(file_path)
                return str(markdown_data)

            # 3. Handle Standard Text/Data Formats (.docx, .txt, .md, .csv, .xlsx, .json)
            elif ext in DOCUMENT_TEXT_FORMATS:
                extracted_text = ""
                
                with fitz.open(file_path) as doc:
                    for page in doc:
                        # Explicit string extraction guard
                        page_string = page.get_text("text")
                        if isinstance(page_string, str):
                            extracted_text += page_string
                        else:
                            extracted_text += str(page_string)
                
                if not extracted_text.strip():
                    raise IngestionError("Document text space came up empty or is corrupted.")
                    
                return extracted_text

            else:
                raise IngestionError(f"Extension '{ext}' must be routed to the Vision Engine.")

        # FIX: Complete block adding except clause to resolve try statement error
        except Exception as exc:
            if isinstance(exc, IngestionError):
                raise exc
            raise IngestionError(
                f"Failed parsing file via Core Ingest Engine: {str(exc)}"
            ) from exc

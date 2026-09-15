from pydantic import BaseModel, Field
from typing import Any, Dict, List

DOCUMENT_LAYOUT_FORMATS = [
    ".pdf", 
    ".epub",
    ".html",
    ".xml", 
    ".xps"  
]

DOCUMENT_TEXT_FORMATS = [
    ".docx",
    ".doc", 
    ".txt", 
    ".md",  
    ".csv", 
    ".xlsx",
    ".json" 
]

CHAT_VISION_FORMATS = [
    ".jpg", 
    ".jpeg",
    ".png", 
    ".webp",
    ".tiff" 
]

ALL_ALLOWED_EXTENSIONS = tuple(DOCUMENT_LAYOUT_FORMATS + DOCUMENT_TEXT_FORMATS + CHAT_VISION_FORMATS)


class DocumentPage(BaseModel):
    """A single page of extracted document content."""

    page_number: int = Field(ge=1, description="1-indexed page number")
    content: str = Field(description="Extracted Markdown or plain text content")


class InternalDocument(BaseModel):
  
    document_id: str = Field(description="Unique UUID reference originating from Django database")
    pages: List[DocumentPage] = Field(
        description="Extracted document pages with 1-indexed page numbers"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Tracks underlying system telemetry: file name, sizing tracking, hashes, page counts"
    )
from pydantic import BaseModel, Field
from typing import Dict, Any

# =====================================================================
# Real-World Allowed File Extensions Configurations
# =====================================================================

# Layout and structural formats handled natively by PyMuPDF / pymupdf4llm
DOCUMENT_LAYOUT_FORMATS = [
    ".pdf", 
    ".epub",
    ".html",
    ".xml", 
    ".xps"  
]

# Text-heavy document formats and clean data tabular strings
DOCUMENT_TEXT_FORMATS = [
    ".docx",
    ".doc", 
    ".txt", 
    ".md",  
    ".csv", 
    ".xlsx",
    ".json" 
]

# Direct image graphic formats uploaded in chat windows requiring Vision/OCR fallback
CHAT_VISION_FORMATS = [
    ".jpg", 
    ".jpeg",
    ".png", 
    ".webp",
    ".tiff" 
]

# Master configuration tuple for application level validation routing gateways
ALL_ALLOWED_EXTENSIONS = tuple(DOCUMENT_LAYOUT_FORMATS + DOCUMENT_TEXT_FORMATS + CHAT_VISION_FORMATS)


# =====================================================================
# Standardized Internal Data Models for Ingestion
# =====================================================================

class InternalDocument(BaseModel):
    """
    Standardized container ensuring all structural file outputs collapse 
    into a single data contract before hitting the chunking steps.
    """
    document_id: str = Field(description="Unique UUID reference originating from Django database")
    content: str = Field(description="Clean layout-aware plain text or converted Markdown payload string")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Tracks underlying system telemetry: file name, sizing tracking, hashes, page counts"
    )
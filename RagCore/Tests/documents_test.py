import os
import pytest
from unittest.mock import MagicMock, patch
from RagCore.Ingestion.pipeline import IngestionPipeline
from RagCore.Ingestion.document_extraction import DocumentExtractionEngine
from RagCore.Ingestion.vision_extraction import VisionExtractionEngine
from RagCore.Ingestion.exceptions import IngestionError

@patch("RagCore.Ingestion.document_extraction.pymupdf4llm.to_markdown")
@patch("os.path.exists")
def test_pipeline_happy_path_pdf_success(mock_exists, mock_to_markdown):

    mock_exists.return_value = True
    mock_to_markdown.return_value = "# Annual Financial Report\nCompany growth is stable at 15%."

    pipeline = IngestionPipeline()
    result = pipeline.run("uploads/financial_report.pdf", "doc-uuid-111")

    assert result.document_id == "doc-uuid-111"
    assert "Annual Financial Report" in result.content
    assert "PyMuPDF" in result.metadata["extraction_engine"]


@patch("RagCore.Ingestion.vision_extraction.Groq")
@patch.object(VisionExtractionEngine, "_encode_image_to_base64")
@patch("os.path.exists")
def test_pipeline_happy_path_direct_image_success(mock_exists, mock_encode, mock_groq_class):

    mock_exists.return_value = True
    mock_encode.return_value = "fake_base64_string"

    mock_client = MagicMock()
    mock_response = MagicMock()
    
    mock_choice_element = MagicMock()
    mock_choice_element.message.content = "| Items | Price |\n|---|---|\n| Coffee | $4.50 |"
    
    mock_response.choices = [mock_choice_element]
    mock_client.chat.completions.create.return_value = mock_response
    mock_groq_class.return_value = mock_client

    pipeline = IngestionPipeline()
    result = pipeline.run("uploads/receipt_screenshot.png", "image-uuid-222")

    assert "Coffee" in result.content
    assert result.metadata["extraction_engine"] == "Groq Vision Engine"


@patch("os.path.exists")
def test_edge_case_file_physically_missing_on_disk(mock_exists):
    """
    EDGE CASE: Django DB has the file path tracking entry, but the physical file 
    got deleted or dropped from disk before Celery executed the worker task.
    """
    mock_exists.return_value = False  # File is gone

    pipeline = IngestionPipeline()
    with pytest.raises(IngestionError) as exc_info:
        pipeline.run("media/deleted_contract.pdf", "doc-uuid-missing")

    assert "File not found" in str(exc_info.value)


@patch("os.path.exists")
def test_edge_case_malicious_unsupported_file_extension(mock_exists):
    """
    EDGE CASE: User attempts to exploit the pipeline by changing a file extension 
    to a dangerous payload or unsupported media binary (.exe, .mp3, .sh).
    """
    mock_exists.return_value = True

    pipeline = IngestionPipeline()
    with pytest.raises(IngestionError) as exc_info:
        pipeline.run("uploads/dangerous_script.exe", "dangerous-uuid")

    assert "completely unsupported" in str(exc_info.value)


@patch("RagCore.Ingestion.pipeline.VisionExtractionEngine.extract_image_text")
@patch("RagCore.Ingestion.pipeline.DocumentExtractionEngine.extract_to_markdown")
@patch("os.path.exists")
def test_edge_case_scanned_pdf_silent_vision_fallback(mock_exists, mock_doc_extract, mock_vision_extract):
    """
    EDGE CASE: A PDF containing only a phone snapshot of text has 0 text layers.
    Document engine raises an empty exception, triggering a silent fallback to Vision OCR.
    """
    mock_exists.return_value = True
    
    # Simulate native text extraction hitting blank character lengths
    mock_doc_extract.side_effect = IngestionError("Document text space came up empty or is corrupted.")
    mock_vision_extract.return_value = "### Extracted Text from Image Scan\nAccount Name: John Doe"

    pipeline = IngestionPipeline()
    result = pipeline.run("uploads/scanned_passport.pdf", "scanned-pdf-uuid")

    assert result.content == "### Extracted Text from Image Scan\nAccount Name: John Doe"
    assert result.metadata["extraction_engine"] == "Groq Vision Fallback (Scanned PDF OCR)"
    mock_doc_extract.assert_called_once()
    mock_vision_extract.assert_called_once()


@patch("RagCore.Ingestion.pipeline.DocumentExtractionEngine.extract_to_markdown")
@patch("os.path.exists")
def test_edge_case_completely_blank_or_whitespace_file(mock_exists, mock_doc_extract):
    """
    EDGE CASE: File looks like a valid document but contains absolutely nothing 
    except blank line breaks, spaces, or tabs. It must be rejected.
    """
    mock_exists.return_value = True
    mock_doc_extract.return_value = "   \n\n     \t   \n   "  # Pure useless string padding

    pipeline = IngestionPipeline()
    with pytest.raises(IngestionError) as exc_info:
        pipeline.run("uploads/blank_sheet.txt", "blank-uuid")

    assert "contains absolutely no readable content" in str(exc_info.value)


@patch("RagCore.Ingestion.pipeline.DocumentExtractionEngine.extract_to_markdown")
@patch("os.path.exists")
def test_edge_case_document_engine_unexpected_hard_crash(mock_exists, mock_doc_extract):
    """
    EDGE CASE: The physical file structure is corrupted, causing PyMuPDF's low-level 
    C-bindings to violently crash or throw a random system ValueError/KeyError.
    """
    mock_exists.return_value = True
    # Simulate a sudden low-level corrupt file system crash
    mock_doc_extract.side_effect = Exception("Fatal memory segmentation fault in MuPDF C-Engine.")

    pipeline = IngestionPipeline()
    with pytest.raises(IngestionError) as exc_info:
        pipeline.run("uploads/corrupt_file.pdf", "corrupt-uuid")

    assert "Document extraction crash" in str(exc_info.value)


@patch("RagCore.Ingestion.pipeline.VisionExtractionEngine.extract_image_text")
@patch("RagCore.Ingestion.pipeline.DocumentExtractionEngine.extract_to_markdown")
@patch("os.path.exists")
def test_edge_case_vision_fallback_also_returns_blank(mock_exists, mock_doc_extract, mock_vision_extract):
    """
    EDGE CASE: A scanned PDF fails text extraction, triggering the vision fallback loop. 
    However, the vision engine also returns nothing (e.g., the user uploaded a completely white square image).
    """
    mock_exists.return_value = True
    mock_doc_extract.side_effect = IngestionError("Document text space came up empty or is corrupted.")
    mock_vision_extract.return_value = "   " # Vision API also returns empty garbage string

    pipeline = IngestionPipeline()
    with pytest.raises(IngestionError) as exc_info:
        pipeline.run("uploads/blank_photo.pdf", "blank-photo-uuid")

    assert "contains absolutely no readable content" in str(exc_info.value)
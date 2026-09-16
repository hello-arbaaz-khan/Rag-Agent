import pytest
from unittest.mock import MagicMock, patch

from RagCore.Ingestion.document import DocumentPage
from RagCore.Ingestion.exceptions import EmptyExtractionError, IngestionError
from RagCore.Ingestion.pipeline import IngestionPipeline
from RagCore.Ingestion.vision_extraction import VisionExtractionEngine


@patch("RagCore.Ingestion.document_extraction.pymupdf4llm.to_markdown")
@patch("os.path.exists")
def test_pipeline_happy_path_pdf_success(mock_exists, mock_to_markdown):
    mock_exists.return_value = True
    mock_to_markdown.return_value = [
        {
            "text": "# Annual Financial Report\nCompany growth is stable at 15%.",
            "metadata": {"page_number": 1},
        }
    ]

    pipeline = IngestionPipeline()
    result = pipeline.run("uploads/financial_report.pdf", "doc-uuid-111")

    assert result.document_id == "doc-uuid-111"
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert "Annual Financial Report" in result.pages[0].content
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

    assert result.pages[0].page_number == 1
    assert "Coffee" in result.pages[0].content
    assert result.metadata["extraction_engine"] == "Groq Vision Engine"


@patch("os.path.exists")
def test_edge_case_file_physically_missing_on_disk(mock_exists):
    mock_exists.return_value = False

    pipeline = IngestionPipeline()

    with pytest.raises(IngestionError) as exc_info:
        pipeline.run("media/deleted_contract.pdf", "doc-uuid-missing")

    assert "File not found" in str(exc_info.value)


@patch("os.path.exists")
def test_edge_case_malicious_unsupported_file_extension(mock_exists):
    mock_exists.return_value = True

    pipeline = IngestionPipeline()

    with pytest.raises(IngestionError) as exc_info:
        pipeline.run("uploads/dangerous_script.exe", "dangerous-uuid")

    assert "completely unsupported" in str(exc_info.value)


@patch("RagCore.Ingestion.pipeline.fitz.open")
@patch("RagCore.Ingestion.pipeline.VisionExtractionEngine.extract_pdf_pages")
@patch("RagCore.Ingestion.pipeline.DocumentExtractionEngine.extract_to_markdown")
@patch("os.path.exists")
def test_edge_case_scanned_pdf_silent_vision_fallback( mock_exists,
    mock_doc_extract,
    mock_vision_extract,
    mock_fitz_open):
    mock_exists.return_value = True

    mock_doc_extract.side_effect = EmptyExtractionError(
        "Document text space came up empty or is corrupted."
    )

    mock_vision_extract.return_value = [
        DocumentPage(page_number=1, content="### Extracted Text from Image Scan\nAccount Name: John Doe"),
        DocumentPage(page_number=2, content="Address: Abbottabad"),
    ]

    pipeline = IngestionPipeline()
    result = pipeline.run("uploads/scanned_passport.pdf", "scanned-pdf-uuid")

    assert len(result.pages) == 2
    assert result.pages[0].page_number == 1
    assert "Account Name" in result.pages[0].content
    assert result.pages[1].page_number == 2
    assert "Address" in result.pages[1].content
    assert result.metadata["extraction_engine"] == "Groq Vision Fallback (Scanned PDF OCR)"

    mock_doc_extract.assert_called_once_with("uploads/scanned_passport.pdf")
    mock_vision_extract.assert_called_once_with("uploads/scanned_passport.pdf")


@patch("RagCore.Ingestion.pipeline.DocumentExtractionEngine.extract_to_markdown")
@patch("os.path.exists")
def test_edge_case_completely_blank_or_whitespace_file(mock_exists, mock_doc_extract):
    mock_exists.return_value = True

    mock_doc_extract.return_value = [
        DocumentPage(page_number=1, content="   \n\n     \t   \n   ")
    ]

    pipeline = IngestionPipeline()

    with pytest.raises(IngestionError) as exc_info:
        pipeline.run("uploads/blank_sheet.txt", "blank-uuid")

    assert "contains absolutely no readable content" in str(exc_info.value)


@patch("RagCore.Ingestion.pipeline.DocumentExtractionEngine.extract_to_markdown")
@patch("os.path.exists")
def test_edge_case_document_engine_unexpected_hard_crash(mock_exists, mock_doc_extract):
    mock_exists.return_value = True

    mock_doc_extract.side_effect = Exception("Fatal memory segmentation fault in MuPDF C-Engine.")

    pipeline = IngestionPipeline()

    with pytest.raises(IngestionError) as exc_info:
        pipeline.run("uploads/corrupt_file.pdf", "corrupt-uuid")

    assert "Document extraction failed" in str(exc_info.value)


@patch("RagCore.Ingestion.pipeline.VisionExtractionEngine.extract_pdf_pages")
@patch("RagCore.Ingestion.pipeline.DocumentExtractionEngine.extract_to_markdown")
@patch("os.path.exists")
def test_edge_case_vision_fallback_also_returns_blank(mock_exists, mock_doc_extract, mock_vision_extract):
    mock_exists.return_value = True

    mock_doc_extract.side_effect = EmptyExtractionError("Document text space came up empty or is corrupted.")
    mock_vision_extract.return_value = []

    pipeline = IngestionPipeline()

    with pytest.raises(IngestionError) as exc_info:
        pipeline.run("uploads/blank_photo.pdf", "blank-photo-uuid")

    assert "contains absolutely no readable content" in str(exc_info.value)

    mock_doc_extract.assert_called_once_with("uploads/blank_photo.pdf")
    mock_vision_extract.assert_called_once_with("uploads/blank_photo.pdf")
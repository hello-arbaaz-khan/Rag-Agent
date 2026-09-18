from pathlib import Path

import pytest

from RagCore.Chunking.pipeline import ChunkingPipeline
from RagCore.Ingestion.pipeline import IngestionPipeline


SAMPLES_DIR = Path(__file__).parent.parent / "Tests" / "Fixtures"/"Pdf_samples" / "sample.docx"
DOCX_SAMPLES_DIR = Path(__file__).parent.parent / "Testes" / "Fixtures" / "Docx_samples" / "sample.pdf"


def get_sample_files(directory: Path, extensions: tuple[str, ...]) -> list[Path]:
    return [
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in extensions
    ]


@pytest.mark.parametrize(
    "file_path",
    get_sample_files(SAMPLES_DIR, (".pdf",)),
    ids=lambda path: path.name,
)
def test_real_pdf_ingestion_to_chunking(file_path):
    ingestion = IngestionPipeline()
    chunking = ChunkingPipeline()

    document = ingestion.process(file_path)
    chunks = chunking.process(document)

    assert chunks
    assert all(chunk.content.strip() for chunk in chunks)
    assert all(chunk.document_id == document.document_id for chunk in chunks)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.page_number is not None for chunk in chunks)


@pytest.mark.parametrize(
    "file_path",
    get_sample_files(DOCX_SAMPLES_DIR, (".docx",)),
    ids=lambda path: path.name,
)
def test_real_docx_ingestion_to_chunking(file_path):
    ingestion = IngestionPipeline()
    chunking = ChunkingPipeline()

    document = ingestion.process(file_path)
    chunks = chunking.process(document)

    assert chunks
    assert all(chunk.content.strip() for chunk in chunks)
    assert all(chunk.document_id == document.document_id for chunk in chunks)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


@pytest.mark.parametrize(
    "file_path",
    get_sample_files(SAMPLES_DIR, (".pdf",))
    + get_sample_files(DOCX_SAMPLES_DIR, (".docx",)),
    ids=lambda path: path.name,
)
def test_real_document_chunking_is_deterministic(file_path):
    ingestion = IngestionPipeline()
    chunking = ChunkingPipeline()

    document = ingestion.process(file_path)

    first = chunking.process(document)
    second = chunking.process(document)

    assert first == second


@pytest.mark.parametrize(
    "file_path",
    get_sample_files(SAMPLES_DIR, (".pdf",))
    + get_sample_files(DOCX_SAMPLES_DIR, (".docx",)),
    ids=lambda path: path.name,
)
def test_real_document_chunk_metadata(file_path):
    ingestion = IngestionPipeline()
    chunking = ChunkingPipeline()

    document = ingestion.process(file_path)
    chunks = chunking.process(document)

    assert chunks

    for chunk in chunks:
        assert chunk.chunk_id
        assert chunk.document_id == document.document_id
        assert chunk.chunk_index >= 0
        assert chunk.content.strip()

    indexes = [chunk.chunk_index for chunk in chunks]

    assert indexes == list(range(len(chunks)))


@pytest.mark.parametrize(
    "file_path",
    get_sample_files(SAMPLES_DIR, (".pdf",))
    + get_sample_files(DOCX_SAMPLES_DIR, (".docx",)),
    ids=lambda path: path.name,
)
def test_real_document_pages_are_preserved(file_path):
    ingestion = IngestionPipeline()
    chunking = ChunkingPipeline()

    document = ingestion.process(file_path)
    chunks = chunking.process(document)

    document_pages = {
        page.page_number
        for page in document.pages
        if page.content and page.content.strip()
    }

    chunk_pages = {
        chunk.page_number
        for chunk in chunks
        if chunk.page_number is not None
    }

    assert chunk_pages.issubset(document_pages)
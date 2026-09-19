from pathlib import Path

import pytest

from RagCore.Ingestion.pipeline import IngestionPipeline
from RagCore.Chunking.pipeline import ChunkingPipeline
from RagCore.Embeddings.embedding import EmbeddingConfig
from RagCore.Embeddings.pipeline import EmbeddingPipeline
from RagCore.Embeddings.provider import SentenceTransformerProvider


FIXTURES_DIR = Path(__file__).parent / "Fixtures"
PDF_DIR = FIXTURES_DIR / "Pdf_samples"
DOCX_DIR = FIXTURES_DIR / "Docx_samples"


def get_pdf_files():
    return sorted(PDF_DIR.glob("*.pdf"))


def get_docx_files():
    return sorted(DOCX_DIR.glob("*.docx"))


@pytest.fixture(scope="module")
def embedding_pipeline():
    config = EmbeddingConfig(
        model="sentence-transformers/all-mpnet-base-v2"
    )
    provider = SentenceTransformerProvider(config)
    return EmbeddingPipeline(provider, config)


@pytest.fixture(scope="module")
def chunks_for_documents():
    ingestion_pipeline = IngestionPipeline()
    chunking_pipeline = ChunkingPipeline()

    def build_chunks(file_path: Path):
        document = ingestion_pipeline.run(
            str(file_path),
            document_id="test-document",
        )

        return chunking_pipeline.process(document)

    return build_chunks


@pytest.mark.parametrize("file_path", get_pdf_files())
def test_real_pdf_embedding(
    file_path,
    chunks_for_documents,
    embedding_pipeline,
):
    chunks = chunks_for_documents(file_path)

    assert chunks

    results = embedding_pipeline.process(chunks)

    assert results
    assert len(results) == len(chunks)


@pytest.mark.parametrize("file_path", get_docx_files())
def test_real_docx_embedding(
    file_path,
    chunks_for_documents,
    embedding_pipeline,
):
    chunks = chunks_for_documents(file_path)

    assert chunks

    results = embedding_pipeline.process(chunks)

    assert results
    assert len(results) == len(chunks)


@pytest.mark.parametrize("file_path", get_pdf_files())
def test_real_pdf_embedding_dimensions(
    file_path,
    chunks_for_documents,
    embedding_pipeline,
):
    chunks = chunks_for_documents(file_path)

    results = embedding_pipeline.process(chunks)

    assert all(result.dimensions == 768 for result in results)
    assert all(len(result.embedding) == 768 for result in results)


@pytest.mark.parametrize("file_path", get_docx_files())
def test_real_docx_embedding_dimensions(
    file_path,
    chunks_for_documents,
    embedding_pipeline,
):
    chunks = chunks_for_documents(file_path)

    results = embedding_pipeline.process(chunks)

    assert all(result.dimensions == 768 for result in results)
    assert all(len(result.embedding) == 768 for result in results)


@pytest.mark.parametrize("file_path", get_pdf_files())
def test_real_pdf_embedding_metadata(
    file_path,
    chunks_for_documents,
    embedding_pipeline,
):
    chunks = chunks_for_documents(file_path)

    results = embedding_pipeline.process(chunks)

    assert all(result.chunk_id for result in results)
    assert all(result.document_id == "test-document" for result in results)
    assert all(result.model == "sentence-transformers/all-mpnet-base-v2" for result in results)


@pytest.mark.parametrize("file_path", get_docx_files())
def test_real_docx_embedding_metadata(
    file_path,
    chunks_for_documents,
    embedding_pipeline,
):
    chunks = chunks_for_documents(file_path)

    results = embedding_pipeline.process(chunks)

    assert all(result.chunk_id for result in results)
    assert all(result.document_id == "test-document" for result in results)
    assert all(result.model == "sentence-transformers/all-mpnet-base-v2" for result in results)


@pytest.mark.parametrize("file_path", get_pdf_files())
def test_real_pdf_embedding_values(
    file_path,
    chunks_for_documents,
    embedding_pipeline,
):
    chunks = chunks_for_documents(file_path)

    results = embedding_pipeline.process(chunks)

    for result in results:
        assert result.embedding
        assert all(isinstance(value, float) for value in result.embedding)


@pytest.mark.parametrize("file_path", get_docx_files())
def test_real_docx_embedding_values(
    file_path,
    chunks_for_documents,
    embedding_pipeline,
):
    chunks = chunks_for_documents(file_path)

    results = embedding_pipeline.process(chunks)

    for result in results:
        assert result.embedding
        assert all(isinstance(value, float) for value in result.embedding)
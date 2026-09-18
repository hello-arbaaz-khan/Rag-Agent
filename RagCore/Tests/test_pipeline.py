import textwrap

from RagCore.Chunking.pipeline import ChunkingPipeline
from RagCore.Ingestion.document import (
    DocumentPage,
    InternalDocument,
)


def test_pipeline_single_page():
    # Ek normal page ko complete Chunking pipeline se pass karte hain.

    document = InternalDocument(
        document_id="doc-1",
        pages=[
            DocumentPage(
                page_number=1,
                content=textwrap.dedent(
                    """
                    # Introduction

                    This is the first paragraph.

                    This is the second paragraph.
                    """
                ),
            )
        ],
        metadata={
            "file_name": "test.pdf",
            "page_count": 1,
        },
    )

    pipeline = ChunkingPipeline()

    chunks = pipeline.process(document)

    assert len(chunks) >= 1

    assert chunks[0].document_id == "doc-1"

    assert chunks[0].page_number == 1

    assert chunks[0].chunk_index == 0

    assert chunks[0].chunk_id == "doc-1:0"

    assert chunks[0].content


def test_pipeline_multiple_pages():
    # Multiple pages independently process honi chahiye.

    document = InternalDocument(
        document_id="doc-2",
        pages=[
            DocumentPage(
                page_number=1,
                content="Page one content.",
            ),
            DocumentPage(
                page_number=2,
                content="Page two content.",
            ),
        ],
        metadata={
            "file_name": "multi-page.pdf",
            "page_count": 2,
        },
    )

    pipeline = ChunkingPipeline()

    chunks = pipeline.process(document)

    assert len(chunks) >= 2

    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2


def test_pipeline_empty_page():
    # Empty page crash nahi karni chahiye.

    document = InternalDocument(
        document_id="doc-3",
        pages=[
            DocumentPage(
                page_number=1,
                content="",
            ),
            DocumentPage(
                page_number=2,
                content="Real content.",
            ),
        ],
        metadata={
            "file_name": "empty-page.pdf",
            "page_count": 2,
        },
    )

    pipeline = ChunkingPipeline()

    chunks = pipeline.process(document)

    assert len(chunks) >= 1

    assert all(chunk.content.strip() for chunk in chunks)


def test_pipeline_preserves_chunk_order():
    # Chunk indexes sequential hone chahiye.

    document = InternalDocument(
        document_id="doc-4",
        pages=[
            DocumentPage(
                page_number=1,
                content="First page.",
            ),
            DocumentPage(
                page_number=2,
                content="Second page.",
            ),
            DocumentPage(
                page_number=3,
                content="Third page.",
            ),
        ],
        metadata={
            "file_name": "ordered.pdf",
            "page_count": 3,
        },
    )

    pipeline = ChunkingPipeline()

    chunks = pipeline.process(document)

    assert [chunk.chunk_index for chunk in chunks] == list(
        range(len(chunks))
    )


def test_pipeline_deterministic():
    # Same document ko do baar process karne par same chunks hone chahiye.

    document = InternalDocument(
        document_id="doc-5",
        pages=[
            DocumentPage(
                page_number=1,
                content=textwrap.dedent(
                    """
                    # Test

                    Some content here.

                    - One
                    - Two
                    """
                ),
            )
        ],
        metadata={
            "file_name": "deterministic.pdf",
            "page_count": 1,
        },
    )

    pipeline = ChunkingPipeline()

    first = pipeline.process(document)
    second = pipeline.process(document)

    assert first == second


def test_pipeline_preserves_structure_metadata():
    # Heading/paragraph ki structural information metadata mein honi chahiye.

    document = InternalDocument(
        document_id="doc-6",
        pages=[
            DocumentPage(
                page_number=1,
                content=textwrap.dedent(
                    """
                    # Introduction

                    Important information.
                    """
                ),
            )
        ],
        metadata={
            "file_name": "metadata.pdf",
            "page_count": 1,
        },
    )

    pipeline = ChunkingPipeline()

    chunks = pipeline.process(document)

    assert chunks

    assert "structure_types" in chunks[0].metadata
    assert "heading" in chunks[0].metadata["structure_types"]
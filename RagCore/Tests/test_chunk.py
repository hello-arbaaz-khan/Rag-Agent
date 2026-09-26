import pytest

from RagCore.Chunking.chunk import Chunk


def test_chunk_creation():

    chunk = Chunk(
        chunk_id="doc-1:0",
        document_id="doc-1",
        content="Hello world",
        page_number=1,
        chunk_index=0,
    )

    assert chunk.chunk_id == "doc-1:0"

    assert chunk.document_id == "doc-1"

    assert chunk.content == "Hello world"

    assert chunk.page_number == 1

    assert chunk.chunk_index == 0


def test_chunk_default_values():

    chunk = Chunk(
        chunk_id="doc-1:0",
        document_id="doc-1",
        content="Text",
        chunk_index=0,
    )

    assert chunk.parent_id is None

    assert chunk.page_number is None

    assert chunk.metadata == {}


def test_chunk_metadata():

    chunk = Chunk(
        chunk_id="doc-1:0",
        document_id="doc-1",
        content="Text",
        chunk_index=0,
        metadata={
            "structure_types": ["heading", "paragraph"],
        },
    )

    assert chunk.metadata["structure_types"] == [
        "heading",
        "paragraph",
    ]


def test_negative_chunk_index_rejected():

    with pytest.raises(ValueError):
        Chunk(
            chunk_id="doc-1:-1",
            document_id="doc-1",
            content="Text",
            chunk_index=-1,
        )
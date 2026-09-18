import pytest

from RagCore.Chunking.chunk import Chunk


def test_chunk_creation():
    # Normal Chunk successfully create hona chahiye.

    chunk = Chunk(
        chunk_id="doc-1:0",
        document_id="doc-1",
        content="Hello world",
        page_number=1,
        chunk_index=0,
    )

    assert chunk.chunk_id == "doc-1:0"
    # Chunk ID preserve hona chahiye.

    assert chunk.document_id == "doc-1"
    # Document ID preserve hona chahiye.

    assert chunk.content == "Hello world"
    # Content exactly preserve hona chahiye.

    assert chunk.page_number == 1
    # Page number preserve hona chahiye.

    assert chunk.chunk_index == 0
    # Chunk ordering preserve honi chahiye.


def test_chunk_default_values():
    # Optional fields ke defaults verify karte hain.

    chunk = Chunk(
        chunk_id="doc-1:0",
        document_id="doc-1",
        content="Text",
        chunk_index=0,
    )

    assert chunk.parent_id is None
    # Parent abhi optional hai.

    assert chunk.page_number is None
    # Page number optional hai.

    assert chunk.metadata == {}
    # Metadata ka default empty dictionary hona chahiye.


def test_chunk_metadata():
    # Custom metadata preserve hona chahiye.

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
    # Structural metadata preserve hona chahiye.


def test_negative_chunk_index_rejected():
    # Negative chunk index invalid hai.

    with pytest.raises(ValueError):
        Chunk(
            chunk_id="doc-1:-1",
            document_id="doc-1",
            content="Text",
            chunk_index=-1,
        )
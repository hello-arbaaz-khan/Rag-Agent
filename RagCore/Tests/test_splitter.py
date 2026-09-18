import pytest

from RagCore.Chunking.parser import StructuralUnit
from RagCore.Chunking.splitter import (
    ChunkSplitter,
    SplitterConfig,
)


def unit(content: str, unit_type: str = "paragraph") -> StructuralUnit:
    # Tests mein StructuralUnit quickly create karne ke liye helper.

    return StructuralUnit(
        unit_type=unit_type,
        content=content,
    )


def test_default_configuration():
    # Default configuration verify karte hain.

    splitter = ChunkSplitter()

    assert splitter.config.chunk_size == 1000
    assert splitter.config.chunk_overlap == 100


def test_custom_configuration():
    # Custom size/overlap accept hone chahiye.

    splitter = ChunkSplitter(
        SplitterConfig(
            chunk_size=500,
            chunk_overlap=50,
        )
    )

    assert splitter.config.chunk_size == 500
    assert splitter.config.chunk_overlap == 50


def test_invalid_chunk_size():
    # Zero/negative chunk size reject honi chahiye.

    with pytest.raises(ValueError):
        ChunkSplitter(
            SplitterConfig(
                chunk_size=0,
                chunk_overlap=0,
            )
        )

    with pytest.raises(ValueError):
        ChunkSplitter(
            SplitterConfig(
                chunk_size=-1,
                chunk_overlap=0,
            )
        )


def test_negative_overlap():
    # Negative overlap invalid hai.

    with pytest.raises(ValueError):
        ChunkSplitter(
            SplitterConfig(
                chunk_size=100,
                chunk_overlap=-1,
            )
        )


def test_overlap_equal_to_size():
    # Overlap chunk size ke equal nahi ho sakta.

    with pytest.raises(ValueError):
        ChunkSplitter(
            SplitterConfig(
                chunk_size=100,
                chunk_overlap=100,
            )
        )


def test_overlap_greater_than_size():
    # Overlap chunk size se bara bhi invalid hai.

    with pytest.raises(ValueError):
        ChunkSplitter(
            SplitterConfig(
                chunk_size=100,
                chunk_overlap=150,
            )
        )


def test_empty_units():
    # Empty input se empty result milna chahiye.

    splitter = ChunkSplitter()

    assert splitter.split([]) == []


def test_whitespace_units():
    # Whitespace-only units ignore honi chahiye.

    splitter = ChunkSplitter()

    units = [
        unit("   "),
        unit("\n\n"),
        unit("Real content"),
    ]

    chunks = splitter.split(units)

    assert chunks == ["Real content"]


def test_units_fit_single_chunk():
    # Small units ek hi chunk mein group honi chahiye.

    splitter = ChunkSplitter(
        SplitterConfig(
            chunk_size=100,
            chunk_overlap=0,
        )
    )

    chunks = splitter.split(
        [
            unit("First paragraph"),
            unit("Second paragraph"),
        ]
    )

    assert len(chunks) == 1
    assert "First paragraph" in chunks[0]
    assert "Second paragraph" in chunks[0]


def test_chunk_size_creates_multiple_chunks():
    # Size limit cross hone par new chunk create hona chahiye.

    splitter = ChunkSplitter(
        SplitterConfig(
            chunk_size=25,
            chunk_overlap=0,
        )
    )

    chunks = splitter.split(
        [
            unit("1234567890"),
            unit("abcdefghij"),
            unit("ABCDEFGHIJ"),
        ]
    )

    assert len(chunks) == 2


def test_zero_overlap():
    # Zero overlap mein previous content repeat nahi hona chahiye.

    splitter = ChunkSplitter(
        SplitterConfig(
            chunk_size=15,
            chunk_overlap=0,
        )
    )

    chunks = splitter.split(
        [
            unit("1234567890"),
            unit("abcdefghij"),
        ]
    )

    assert len(chunks) == 2
    assert chunks[0] == "1234567890"
    assert chunks[1] == "abcdefghij"


def test_overlap():
    # Configured overlap next chunk mein appear hona chahiye.

    splitter = ChunkSplitter(
        SplitterConfig(
            chunk_size=20,
            chunk_overlap=5,
        )
    )

    chunks = splitter.split(
        [
            unit("1234567890"),
            unit("abcdefghij"),
        ]
    )

    assert len(chunks) == 2
    assert "67890" in chunks[1]


def test_large_single_unit():
    # Single unit chunk_size se bara ho to split hona chahiye.

    splitter = ChunkSplitter(
        SplitterConfig(
            chunk_size=10,
            chunk_overlap=2,
        )
    )

    content = "abcdefghijklmnopqrstuvwxyz"

    chunks = splitter.split([unit(content)])

    assert len(chunks) > 1

    for chunk in chunks:
        # Har generated piece inspect karte hain.

        assert len(chunk) <= 10


def test_large_unit_preserves_content():
    # Large unit split hone ke baad original content completely lose nahi hona chahiye.

    splitter = ChunkSplitter(
        SplitterConfig(
            chunk_size=10,
            chunk_overlap=2,
        )
    )

    content = "abcdefghijklmnopqrstuvwxyz"

    chunks = splitter.split([unit(content)])

    combined = "".join(chunks)

    for character in content:
        # Har original character kisi na kisi chunk mein hona chahiye.

        assert character in combined


def test_structural_units_preserve_order():
    # Structural unit ka order change nahi hona chahiye.

    splitter = ChunkSplitter(
        SplitterConfig(
            chunk_size=100,
            chunk_overlap=0,
        )
    )

    chunks = splitter.split(
        [
            unit("FIRST"),
            unit("SECOND"),
            unit("THIRD"),
        ]
    )

    assert chunks == ["FIRST\n\nSECOND\n\nTHIRD"]


def test_deterministic_splitter():
    # Same input se same chunks generate hone chahiye.

    splitter = ChunkSplitter(
        SplitterConfig(
            chunk_size=30,
            chunk_overlap=5,
        )
    )

    units = [
        unit("First"),
        unit("Second"),
        unit("Third"),
        unit("Fourth"),
    ]

    first = splitter.split(units)
    second = splitter.split(units)

    assert first == second
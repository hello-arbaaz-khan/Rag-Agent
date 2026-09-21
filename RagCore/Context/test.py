from RagCore.Context.builder import ContextBuilder
from RagCore.Context.context import ContextConfig
from RagCore.Retrieval.retrieval import RetrievalResult


def make_result(
    chunk_id,
    document_id,
    content,
    chunk_index,
    page_number=None,
):
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        content=content,
        score=0.90,
        page_number=page_number,
        chunk_index=chunk_index,
    )


def test_build_context_from_candidates():
    candidates = [
        make_result(
            "chunk-1",
            "doc-1",
            "First content",
            0,
        ),
        make_result(
            "chunk-2",
            "doc-1",
            "Second content",
            1,
        ),
    ]

    builder = ContextBuilder()

    context = builder.build(candidates)

    assert context.text == (
        "First content"
        "\n\n---\n\n"
        "Second content"
    )


def test_build_context_preserves_source_information():
    candidates = [
        make_result(
            "chunk-1",
            "doc-1",
            "First content",
            0,
            page_number=3,
        )
    ]

    builder = ContextBuilder()

    context = builder.build(candidates)

    assert context.sources == [
        {
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "page_number": 3,
            "chunk_index": 0,
            "metadata": {},
        }
    ]


def test_build_empty_context():
    builder = ContextBuilder()

    context = builder.build([])

    assert context.text == ""
    assert context.sources == []


def test_build_context_respects_max_chunks():
    candidates = [
        make_result(
            "chunk-1",
            "doc-1",
            "Content 1",
            0,
        ),
        make_result(
            "chunk-2",
            "doc-1",
            "Content 2",
            1,
        ),
        make_result(
            "chunk-3",
            "doc-1",
            "Content 3",
            2,
        ),
    ]

    config = ContextConfig(max_chunks=2)

    builder = ContextBuilder(config)

    context = builder.build(candidates)

    assert len(context.sources) == 2
    assert "Content 1" in context.text
    assert "Content 2" in context.text
    assert "Content 3" not in context.text


def test_build_context_preserves_candidate_order():
    candidates = [
        make_result(
            "chunk-2",
            "doc-1",
            "Second",
            1,
        ),
        make_result(
            "chunk-1",
            "doc-1",
            "First",
            0,
        ),
    ]

    builder = ContextBuilder()

    context = builder.build(candidates)

    assert context.text == (
        "Second"
        "\n\n---\n\n"
        "First"
    )


def test_context_config_default_max_chunks():
    config = ContextConfig()

    assert config.max_chunks == 5


def test_context_config_rejects_invalid_max_chunks():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ContextConfig(max_chunks=0)
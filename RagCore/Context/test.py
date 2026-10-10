from RagCore.Context.builder import ContextBuilder
from RagCore.Context.context import ContextConfig
from RagCore.Retrieval.retrieval import RetrievalResult


def make_result(
    chunk_id,
    document_id,
    content,
    *,
    page_number=None,
    metadata=None,
    score=0.9,
):
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        content=content,
        score=score,
        page_number=page_number,
        chunk_index=0,
        metadata=metadata or {},
    )


def test_context_includes_evidence_from_multiple_documents():
    builder = ContextBuilder(
        ContextConfig(max_chunks=5)
    )

    candidates = [
        make_result(
            "a1",
            "doc-a",
            "Document A discusses a trade agreement.",
            page_number=2,
            metadata={"filename": "Report-A.pdf"},
        ),
        make_result(
            "a2",
            "doc-a",
            "Document A also describes its implementation.",
            page_number=3,
            metadata={"filename": "Report-A.pdf"},
        ),
        make_result(
            "b1",
            "doc-b",
            "Document B discusses a different agreement.",
            page_number=5,
            metadata={"filename": "Report-B.pdf"},
        ),
    ]

    context = builder.build(candidates)

    assert "Report-A.pdf" in context.text
    assert "Report-B.pdf" in context.text
    assert "Page: 2" in context.text
    assert "Page: 5" in context.text
    assert len(context.sources) == 3


def test_context_represents_each_document_before_extra_chunks():
    builder = ContextBuilder(
        ContextConfig(max_chunks=3)
    )

    candidates = [
        make_result("a1", "doc-a", "A first excerpt."),
        make_result("a2", "doc-a", "A second excerpt."),
        make_result("a3", "doc-a", "A third excerpt."),
        make_result("b1", "doc-b", "B first excerpt."),
    ]

    context = builder.build(candidates)

    document_ids = {
        source["document_id"]
        for source in context.sources
    }

    assert document_ids == {"doc-a", "doc-b"}
    assert len(context.sources) == 3


def test_context_deduplicates_identical_content():
    builder = ContextBuilder()

    context = builder.build(
        [
            make_result("a1", "doc-a", "Same content."),
            make_result("b1", "doc-b", "  SAME   CONTENT. "),
        ]
    )

    assert len(context.sources) == 1


def test_context_uses_document_id_when_name_is_unavailable():
    context = ContextBuilder().build(
        [
            make_result(
                "a1",
                "doc-a",
                "Evidence without a document title.",
                page_number=7,
            )
        ]
    )

    assert "Document: doc-a" in context.text
    assert "Page: 7" in context.text


def test_context_respects_maximum_chunk_count():
    context = ContextBuilder(
        ContextConfig(max_chunks=2)
    ).build(
        [
            make_result("a1", "doc-a", "First excerpt."),
            make_result("b1", "doc-b", "Second excerpt."),
            make_result("c1", "doc-c", "Third excerpt."),
        ]
    )

    assert len(context.sources) == 2
    assert "Third excerpt." not in context.text


def test_empty_candidates_produce_empty_context():
    context = ContextBuilder().build([])

    assert context.text == ""
    assert context.sources == []
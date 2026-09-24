import math

import pytest
from pydantic import ValidationError

from RagCore.Chunking.chunk import Chunk
from RagCore.ErrorsHandle.exceptions import RetrievalError
from RagCore.Retrieval.bm25 import BM25Retriever
from RagCore.Retrieval.hybrid import HybridRetriever
from RagCore.Retrieval.pipeline import RetrievalPipeline
from RagCore.Retrieval.retrieval import (
    RetrievalConfig,
    RetrievalMode,
    RetrievalResult,
)


class FakeRepository:
    def __init__(self, results=None):
        self.results = results or []
        self.calls = []

    def search(
        self,
        query_embedding,
        top_k,
        document_ids=None,
    ):
        self.calls.append(
            (
                query_embedding,
                top_k,
                document_ids,
            )
        )

        results = self.results

        if document_ids is not None:
            results = [
                result
                for result in results
                if result.document_id in document_ids
            ]

        return results[:top_k]


class BrokenRepository:
    def search(
        self,
        query_embedding,
        top_k,
        document_ids=None,
    ):
        raise RuntimeError("database unavailable")


class FakeVectorRetriever:
    def __init__(self, results=None):
        self.results = results or []
        self.calls = []

    def retrieve(
        self,
        query_embedding,
        *,
        top_k,
        document_ids=None,
    ):
        self.calls.append(
            (
                query_embedding,
                top_k,
                document_ids,
            )
        )

        results = self.results

        if document_ids is not None:
            results = [
                result
                for result in results
                if result.document_id in document_ids
            ]

        return results[:top_k]


class FakeBM25Retriever:
    def __init__(self, results=None):
        self.results = results or []
        self.calls = []

    def search(
        self,
        query,
        *,
        top_k,
        document_ids=None,
    ):
        self.calls.append(
            (
                query,
                top_k,
                document_ids,
            )
        )

        results = self.results

        if document_ids is not None:
            results = [
                result
                for result in results
                if result.document_id in document_ids
            ]

        return results[:top_k]


def make_result(
    chunk_id,
    document_id,
    score,
    chunk_index,
    metadata=None,
):
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        content=f"content-{chunk_id}",
        score=score,
        chunk_index=chunk_index,
        metadata=metadata or {},
    )


def make_chunk(
    chunk_id,
    document_id,
    content,
    chunk_index=0,
    parent_id=None,
    page_number=None,
    metadata=None,
):
    return Chunk(
        chunk_id=chunk_id,
        document_id=document_id,
        parent_id=parent_id,
        content=content,
        page_number=page_number,
        chunk_index=chunk_index,
        metadata=metadata or {},
    )


def test_retrieval_config_defaults():
    config = RetrievalConfig()

    assert config.top_k == 20
    assert config.dimensions == 384
    assert config.mode == RetrievalMode.VECTOR
    assert config.candidate_k == 20
    assert config.rrf_k == 60


def test_retrieval_config_accepts_hybrid_mode():
    config = RetrievalConfig(
        mode=RetrievalMode.HYBRID,
    )

    assert config.mode == RetrievalMode.HYBRID


def test_retrieval_config_rejects_invalid_values():
    with pytest.raises(ValidationError):
        RetrievalConfig(top_k=0)

    with pytest.raises(ValidationError):
        RetrievalConfig(dimensions=0)

    with pytest.raises(ValidationError):
        RetrievalConfig(candidate_k=0)

    with pytest.raises(ValidationError):
        RetrievalConfig(rrf_k=0)


def test_retrieve_uses_default_top_k_20():
    repository = FakeRepository()
    pipeline = RetrievalPipeline(repository)

    pipeline.retrieve([0.0] * 384)

    assert repository.calls[0][1] == 20


def test_retrieve_respects_custom_top_k():
    repository = FakeRepository(
        [
            make_result("1", "doc-1", 0.95, 0),
            make_result("2", "doc-1", 0.90, 1),
            make_result("3", "doc-1", 0.85, 2),
        ]
    )

    pipeline = RetrievalPipeline(repository)

    results = pipeline.retrieve(
        [0.0] * 384,
        top_k=2,
    )

    assert len(results) == 2
    assert [
        result.chunk_id
        for result in results
    ] == ["1", "2"]


def test_retrieve_empty_repository_returns_empty_list():
    repository = FakeRepository()
    pipeline = RetrievalPipeline(repository)

    results = pipeline.retrieve(
        [0.0] * 384,
    )

    assert results == []


def test_retrieve_preserves_similarity_order():
    repository = FakeRepository(
        [
            make_result("1", "doc-1", 0.95, 0),
            make_result("2", "doc-1", 0.90, 1),
            make_result("3", "doc-1", 0.80, 2),
        ]
    )

    pipeline = RetrievalPipeline(repository)

    results = pipeline.retrieve(
        [0.0] * 384,
        top_k=3,
    )

    assert [
        result.score
        for result in results
    ] == [
        0.95,
        0.90,
        0.80,
    ]


def test_retrieve_rejects_empty_embedding():
    pipeline = RetrievalPipeline(
        FakeRepository()
    )

    with pytest.raises(RetrievalError):
        pipeline.retrieve([])


def test_retrieve_rejects_wrong_embedding_dimensions():
    pipeline = RetrievalPipeline(
        FakeRepository()
    )

    with pytest.raises(RetrievalError):
        pipeline.retrieve(
            [0.0] * 383,
        )


def test_retrieve_rejects_non_numeric_embedding():
    pipeline = RetrievalPipeline(
        FakeRepository()
    )

    with pytest.raises(RetrievalError):
        pipeline.retrieve(
            [0.0] * 383 + ["invalid"],
        )


@pytest.mark.parametrize(
    "value",
    [
        math.nan,
        math.inf,
        -math.inf,
    ],
)
def test_retrieve_rejects_non_finite_embedding(value):
    pipeline = RetrievalPipeline(
        FakeRepository()
    )

    with pytest.raises(RetrievalError):
        pipeline.retrieve(
            [0.0] * 383 + [value],
        )


@pytest.mark.parametrize(
    "top_k",
    [
        0,
        -1,
    ],
)
def test_retrieve_rejects_invalid_top_k(top_k):
    pipeline = RetrievalPipeline(
        FakeRepository()
    )

    with pytest.raises(RetrievalError):
        pipeline.retrieve(
            [0.0] * 384,
            top_k=top_k,
        )


def test_retrieve_rejects_invalid_document_filter():
    pipeline = RetrievalPipeline(
        FakeRepository()
    )

    with pytest.raises(RetrievalError):
        pipeline.retrieve(
            [0.0] * 384,
            document_ids=[
                "doc-1",
                "",
            ],
        )


def test_retrieve_passes_document_filter():
    repository = FakeRepository(
        [
            make_result(
                "1",
                "doc-1",
                0.95,
                0,
            ),
        ]
    )

    pipeline = RetrievalPipeline(repository)

    pipeline.retrieve(
        [0.0] * 384,
        document_ids=["doc-1"],
    )

    assert repository.calls[0][2] == [
        "doc-1"
    ]


def test_retrieve_filters_results_by_document_ids():
    repository = FakeRepository(
        [
            make_result(
                "1",
                "doc-1",
                0.95,
                0,
            ),
            make_result(
                "2",
                "doc-2",
                0.90,
                1,
            ),
        ]
    )

    pipeline = RetrievalPipeline(repository)

    results = pipeline.retrieve(
        [0.0] * 384,
        document_ids=["doc-1"],
    )

    assert [
        result.document_id
        for result in results
    ] == ["doc-1"]


def test_retrieve_wraps_repository_error():
    pipeline = RetrievalPipeline(
        BrokenRepository()
    )

    with pytest.raises(
        RetrievalError,
        match="database unavailable",
    ):
        pipeline.retrieve(
            [0.0] * 384,
        )


def test_bm25_empty_index_returns_empty():
    retriever = BM25Retriever()

    results = retriever.search(
        "python",
    )

    assert results == []


def test_bm25_indexes_chunks():
    chunks = [
        make_chunk(
            "chunk-1",
            "doc-1",
            "Python programming language",
        ),
        make_chunk(
            "chunk-2",
            "doc-1",
            "Django web framework",
        ),
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "Python",
        top_k=2,
    )

    assert results
    assert results[0].chunk_id == "chunk-1"


def test_bm25_matches_exact_terms():
    chunks = [
        make_chunk(
            "chunk-1",
            "doc-1",
            "The API error code is E401.",
        ),
        make_chunk(
            "chunk-2",
            "doc-1",
            "The API handles authentication.",
        ),
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "E401",
        top_k=2,
    )

    assert results
    assert results[0].chunk_id == "chunk-1"


def test_bm25_is_case_insensitive():
    chunks = [
        make_chunk(
            "chunk-1",
            "doc-1",
            "Python Programming",
        ),
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "python",
    )

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"


def test_bm25_respects_top_k():
    chunks = [
        make_chunk(
            "chunk-1",
            "doc-1",
            "python programming",
        ),
        make_chunk(
            "chunk-2",
            "doc-1",
            "python development",
        ),
        make_chunk(
            "chunk-3",
            "doc-1",
            "python testing",
        ),
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "python",
        top_k=2,
    )

    assert len(results) == 2


def test_bm25_respects_document_filter():
    chunks = [
        make_chunk(
            "chunk-1",
            "doc-1",
            "python programming",
        ),
        make_chunk(
            "chunk-2",
            "doc-2",
            "python programming",
        ),
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "python",
        document_ids=["doc-2"],
    )

    assert len(results) == 1
    assert results[0].document_id == "doc-2"


def test_bm25_returns_empty_for_unknown_term():
    chunks = [
        make_chunk(
            "chunk-1",
            "doc-1",
            "python programming",
        ),
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "nonexistentterm",
    )

    assert results == []


def test_bm25_rejects_empty_query():
    retriever = BM25Retriever()

    with pytest.raises(RetrievalError):
        retriever.search("")


def test_bm25_rejects_whitespace_query():
    retriever = BM25Retriever()

    with pytest.raises(RetrievalError):
        retriever.search("   ")


@pytest.mark.parametrize(
    "top_k",
    [
        0,
        -1,
    ],
)
def test_bm25_rejects_invalid_top_k(top_k):
    retriever = BM25Retriever()

    with pytest.raises(RetrievalError):
        retriever.search(
            "python",
            top_k=top_k,
        )


def test_bm25_rejects_invalid_document_filter():
    retriever = BM25Retriever()

    with pytest.raises(RetrievalError):
        retriever.search(
            "python",
            document_ids=["doc-1", ""],
        )


def test_bm25_preserves_chunk_metadata():
    chunk = make_chunk(
        "chunk-1",
        "doc-1",
        "Python programming",
        chunk_index=4,
        page_number=7,
        metadata={
            "section": "Introduction",
        },
    )

    retriever = BM25Retriever([chunk])

    results = retriever.search(
        "python",
    )

    assert results[0].chunk_id == "chunk-1"
    assert results[0].document_id == "doc-1"
    assert results[0].content == "Python programming"
    assert results[0].chunk_index == 4
    assert results[0].page_number == 7
    assert results[0].metadata == {
        "section": "Introduction",
    }


def test_hybrid_retrieval_uses_both_retrievers():
    vector_results = [
        make_result(
            "chunk-vector",
            "doc-1",
            0.95,
            0,
        ),
    ]

    bm25_results = [
        make_result(
            "chunk-bm25",
            "doc-1",
            4.5,
            1,
        ),
    ]

    vector = FakeVectorRetriever(
        vector_results,
    )

    bm25 = FakeBM25Retriever(
        bm25_results,
    )

    hybrid = HybridRetriever(
        vector,
        bm25,
    )

    results = hybrid.retrieve(
        query="python",
        query_embedding=[0.1] * 384,
        top_k=2,
    )

    assert len(results) == 2

    assert vector.calls[0][1] == 2
    assert bm25.calls[0][1] == 2
    assert bm25.calls[0][0] == "python"


def test_hybrid_document_in_both_retrievers_gets_higher_rrf_score():
    shared = make_result(
        "shared",
        "doc-1",
        0.90,
        0,
    )

    vector_only = make_result(
        "vector-only",
        "doc-1",
        0.95,
        1,
    )

    bm25_only = make_result(
        "bm25-only",
        "doc-1",
        5.0,
        2,
    )

    vector = FakeVectorRetriever(
        [
            shared,
            vector_only,
        ]
    )

    bm25 = FakeBM25Retriever(
        [
            shared,
            bm25_only,
        ]
    )

    hybrid = HybridRetriever(
        vector,
        bm25,
        rrf_k=60,
    )

    results = hybrid.retrieve(
        query="python",
        query_embedding=[0.1] * 384,
        top_k=3,
    )

    assert results[0].chunk_id == "shared"

    assert results[0].metadata["rrf_score"] > (
        results[1].metadata["rrf_score"]
    )


def test_hybrid_handles_vector_only_results():
    vector = FakeVectorRetriever(
        [
            make_result(
                "vector-only",
                "doc-1",
                0.95,
                0,
            ),
        ]
    )

    bm25 = FakeBM25Retriever()

    hybrid = HybridRetriever(
        vector,
        bm25,
    )

    results = hybrid.retrieve(
        query="python",
        query_embedding=[0.1] * 384,
    )

    assert len(results) == 1
    assert results[0].chunk_id == "vector-only"


def test_hybrid_handles_bm25_only_results():
    vector = FakeVectorRetriever()

    bm25 = FakeBM25Retriever(
        [
            make_result(
                "bm25-only",
                "doc-1",
                5.0,
                0,
            ),
        ]
    )

    hybrid = HybridRetriever(
        vector,
        bm25,
    )

    results = hybrid.retrieve(
        query="python",
        query_embedding=[0.1] * 384,
    )

    assert len(results) == 1
    assert results[0].chunk_id == "bm25-only"


def test_hybrid_handles_empty_results():
    hybrid = HybridRetriever(
        FakeVectorRetriever(),
        FakeBM25Retriever(),
    )

    results = hybrid.retrieve(
        query="python",
        query_embedding=[0.1] * 384,
    )

    assert results == []


def test_hybrid_respects_top_k():
    vector = FakeVectorRetriever(
        [
            make_result(
                "1",
                "doc-1",
                0.9,
                0,
            ),
            make_result(
                "2",
                "doc-1",
                0.8,
                1,
            ),
            make_result(
                "3",
                "doc-1",
                0.7,
                2,
            ),
        ]
    )

    bm25 = FakeBM25Retriever()

    hybrid = HybridRetriever(
        vector,
        bm25,
    )

    results = hybrid.retrieve(
        query="python",
        query_embedding=[0.1] * 384,
        top_k=2,
    )

    assert len(results) == 2


def test_hybrid_passes_document_filter_to_both_retrievers():
    vector = FakeVectorRetriever()
    bm25 = FakeBM25Retriever()

    hybrid = HybridRetriever(
        vector,
        bm25,
    )

    hybrid.retrieve(
        query="python",
        query_embedding=[0.1] * 384,
        document_ids=[
            "doc-1",
            "doc-2",
        ],
    )

    assert vector.calls[0][2] == [
        "doc-1",
        "doc-2",
    ]

    assert bm25.calls[0][2] == [
        "doc-1",
        "doc-2",
    ]


def test_hybrid_rejects_empty_query():
    hybrid = HybridRetriever(
        FakeVectorRetriever(),
        FakeBM25Retriever(),
    )

    with pytest.raises(RetrievalError):
        hybrid.retrieve(
            query="",
            query_embedding=[0.1] * 384,
        )


def test_hybrid_rejects_invalid_top_k():
    hybrid = HybridRetriever(
        FakeVectorRetriever(),
        FakeBM25Retriever(),
    )

    with pytest.raises(RetrievalError):
        hybrid.retrieve(
            query="python",
            query_embedding=[0.1] * 384,
            top_k=0,
        )


def test_hybrid_rejects_invalid_candidate_k():
    hybrid = HybridRetriever(
        FakeVectorRetriever(),
        FakeBM25Retriever(),
    )

    with pytest.raises(RetrievalError):
        hybrid.retrieve(
            query="python",
            query_embedding=[0.1] * 384,
            candidate_k=0,
        )


def test_hybrid_rejects_invalid_document_filter():
    hybrid = HybridRetriever(
        FakeVectorRetriever(),
        FakeBM25Retriever(),
    )

    with pytest.raises(RetrievalError):
        hybrid.retrieve(
            query="python",
            query_embedding=[0.1] * 384,
            document_ids=[
                "doc-1",
                "",
            ],
        )


def test_hybrid_rejects_invalid_rrf_k():
    with pytest.raises(ValueError):
        HybridRetriever(
            FakeVectorRetriever(),
            FakeBM25Retriever(),
            rrf_k=0,
        )


def test_hybrid_preserves_vector_metadata():
    vector_result = make_result(
        "chunk-1",
        "doc-1",
        0.95,
        3,
        metadata={
            "section": "Methods",
        },
    )

    hybrid = HybridRetriever(
        FakeVectorRetriever(
            [vector_result],
        ),
        FakeBM25Retriever(),
    )

    results = hybrid.retrieve(
        query="python",
        query_embedding=[0.1] * 384,
    )

    assert results[0].chunk_id == "chunk-1"
    assert results[0].document_id == "doc-1"
    assert results[0].chunk_index == 3
    assert results[0].metadata["section"] == "Methods"
    assert "rrf_score" in results[0].metadata


def test_hybrid_pipeline_vector_mode_keeps_existing_behavior():
    repository = FakeRepository(
        [
            make_result(
                "1",
                "doc-1",
                0.95,
                0,
            ),
        ]
    )

    config = RetrievalConfig(
        mode=RetrievalMode.VECTOR,
    )

    pipeline = RetrievalPipeline(
        repository,
        config,
    )

    results = pipeline.retrieve(
        [0.0] * 384,
    )

    assert len(results) == 1
    assert results[0].chunk_id == "1"


def test_hybrid_pipeline_requires_hybrid_retriever():
    config = RetrievalConfig(
        mode=RetrievalMode.HYBRID,
    )

    pipeline = RetrievalPipeline(
        FakeRepository(),
        config,
    )

    with pytest.raises(
        RetrievalError,
        match="Hybrid retrieval is not configured",
    ):
        pipeline.retrieve(
            [0.0] * 384,
            query="python",
        )


def test_hybrid_pipeline_requires_query():
    config = RetrievalConfig(
        mode=RetrievalMode.HYBRID,
    )

    hybrid = HybridRetriever(
        FakeVectorRetriever(),
        FakeBM25Retriever(),
    )

    pipeline = RetrievalPipeline(
        FakeRepository(),
        config,
        hybrid_retriever=hybrid,
    )

    with pytest.raises(
        RetrievalError,
        match="Query is required",
    ):
        pipeline.retrieve(
            [0.0] * 384,
        )


def test_hybrid_pipeline_passes_query_to_hybrid_retriever():
    vector = FakeVectorRetriever()
    bm25 = FakeBM25Retriever()

    hybrid = HybridRetriever(
        vector,
        bm25,
    )

    config = RetrievalConfig(
        mode=RetrievalMode.HYBRID,
    )

    pipeline = RetrievalPipeline(
        FakeRepository(),
        config,
        hybrid_retriever=hybrid,
    )

    pipeline.retrieve(
        [0.0] * 384,
        query="python django",
        top_k=5,
    )

    assert bm25.calls[0][0] == "python django"
    assert vector.calls[0][1] == 20
    assert bm25.calls[0][1] == 20
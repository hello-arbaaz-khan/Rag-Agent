import pytest
from pydantic import ValidationError

from RagCore.ErrorsHandle.exceptions import RerankingError
from RagCore.Reranking.pipeline import RerankingPipeline
from RagCore.Reranking.reranking import RerankingConfig
from RagCore.Retrieval.retrieval import RetrievalResult


class FakeRerankerProvider:
    def __init__(self, scores=None):
        self.scores = scores or []
        self.calls = []

    def score(self, query, contents):
        self.calls.append((query, contents))
        return self.scores


def make_result(
    chunk_id,
    document_id,
    score,
    chunk_index,
    content=None,
):
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        content=(f"content-{chunk_id}" if content is None else content),
        score=score,
        chunk_index=chunk_index,
    )


def test_reranking_config_defaults():
    config = RerankingConfig()

    assert config.top_k == 5


def test_reranking_config_rejects_invalid_top_k():
    with pytest.raises(ValidationError):
        RerankingConfig(top_k=0)


def test_rerank_returns_top_k_results():
    candidates = [
        make_result("1", "doc-1", 0.90, 0),
        make_result("2", "doc-1", 0.80, 1),
        make_result("3", "doc-1", 0.70, 2),
    ]

    provider = FakeRerankerProvider(
        scores=[0.20, 0.95, 0.70]
    )

    pipeline = RerankingPipeline(provider)

    results = pipeline.rerank(
        "test query",
        candidates,
        top_k=2,
    )

    assert len(results) == 2
    assert [result.chunk_id for result in results] == [
        "2",
        "3",
    ]


def test_rerank_orders_by_rerank_score():
    candidates = [
        make_result("1", "doc-1", 0.99, 0),
        make_result("2", "doc-1", 0.90, 1),
        make_result("3", "doc-1", 0.80, 2),
    ]

    provider = FakeRerankerProvider(
        scores=[0.10, 0.90, 0.50]
    )

    pipeline = RerankingPipeline(provider)

    results = pipeline.rerank(
        "test query",
        candidates,
        top_k=3,
    )

    assert [result.chunk_id for result in results] == [
        "2",
        "3",
        "1",
    ]

    assert [
        result.metadata["rerank_score"]
        for result in results
    ] == [
        0.90,
        0.50,
        0.10,
    ]


def test_rerank_preserves_original_retrieval_score():
    candidates = [
        make_result("1", "doc-1", 0.95, 0),
        make_result("2", "doc-1", 0.80, 1),
    ]

    provider = FakeRerankerProvider(
        scores=[0.20, 0.90]
    )

    pipeline = RerankingPipeline(provider)

    results = pipeline.rerank(
        "test query",
        candidates,
        top_k=2,
    )

    result = next(
        result
        for result in results
        if result.chunk_id == "1"
    )

    assert result.score == 0.95
    assert result.metadata["rerank_score"] == 0.20


def test_rerank_passes_query_and_contents_to_provider():
    candidates = [
        make_result("1", "doc-1", 0.90, 0),
        make_result("2", "doc-1", 0.80, 1),
    ]

    provider = FakeRerankerProvider(
        scores=[0.90, 0.80]
    )

    pipeline = RerankingPipeline(provider)

    pipeline.rerank(
        "my question",
        candidates,
    )

    assert provider.calls == [
        (
            "my question",
            [
                "content-1",
                "content-2",
            ],
        )
    ]


def test_rerank_empty_candidates_returns_empty_list():
    provider = FakeRerankerProvider()

    pipeline = RerankingPipeline(provider)

    results = pipeline.rerank(
        "test query",
        [],
    )

    assert results == []
    assert provider.calls == []


def test_rerank_rejects_invalid_top_k():
    provider = FakeRerankerProvider()

    pipeline = RerankingPipeline(provider)

    with pytest.raises(RerankingError):
        pipeline.rerank(
            "test query",
            [],
            top_k=0,
        )


def test_rerank_rejects_negative_top_k():
    provider = FakeRerankerProvider()

    pipeline = RerankingPipeline(provider)

    with pytest.raises(RerankingError):
        pipeline.rerank(
            "test query",
            [],
            top_k=-1,
        )


def test_rerank_top_k_greater_than_candidates():
    candidates = [
        make_result("1", "doc-1", 0.90, 0),
        make_result("2", "doc-1", 0.80, 1),
    ]

    provider = FakeRerankerProvider(
        scores=[0.90, 0.80]
    )

    pipeline = RerankingPipeline(provider)

    results = pipeline.rerank(
        "test query",
        candidates,
        top_k=5,
    )

    assert len(results) == 2


def test_rerank_top_k_equal_to_candidates():
    candidates = [
        make_result("1", "doc-1", 0.90, 0),
        make_result("2", "doc-1", 0.80, 1),
    ]

    provider = FakeRerankerProvider(
        scores=[0.90, 0.80]
    )

    pipeline = RerankingPipeline(provider)

    results = pipeline.rerank(
        "test query",
        candidates,
        top_k=2,
    )

    assert len(results) == 2


def test_rerank_rejects_empty_query():
    provider = FakeRerankerProvider()

    pipeline = RerankingPipeline(provider)

    with pytest.raises(RerankingError):
        pipeline.rerank(
            "",
            [],
        )


def test_rerank_rejects_non_string_query():
    provider = FakeRerankerProvider()

    pipeline = RerankingPipeline(provider)

    with pytest.raises(RerankingError):
        pipeline.rerank(
            None,
            [],
        )


def test_rerank_rejects_invalid_candidates():
    provider = FakeRerankerProvider()

    pipeline = RerankingPipeline(provider)

    with pytest.raises(RerankingError):
        pipeline.rerank(
            "test query",
            ["invalid"],
        )


def test_rerank_rejects_empty_candidate_content():
    candidates = [
        make_result(
            "1",
            "doc-1",
            0.90,
            0,
            content="",
        )
    ]

    provider = FakeRerankerProvider(
        scores=[0.90]
    )

    pipeline = RerankingPipeline(provider)

    with pytest.raises(RerankingError):
        pipeline.rerank(
            "test query",
            candidates,
        )


def test_rerank_rejects_wrong_number_of_scores():
    candidates = [
        make_result("1", "doc-1", 0.90, 0),
        make_result("2", "doc-1", 0.80, 1),
    ]

    provider = FakeRerankerProvider(
        scores=[0.90]
    )

    pipeline = RerankingPipeline(provider)

    with pytest.raises(RerankingError):
        pipeline.rerank(
            "test query",
            candidates,
        )


def test_rerank_rejects_non_numeric_score():
    candidates = [
        make_result("1", "doc-1", 0.90, 0),
    ]

    provider = FakeRerankerProvider(
        scores=["invalid"]
    )

    pipeline = RerankingPipeline(provider)

    with pytest.raises(RerankingError):
        pipeline.rerank(
            "test query",
            candidates,
        )


def test_rerank_wraps_provider_error():
    candidates = [
        make_result("1", "doc-1", 0.90, 0),
    ]

    class BrokenProvider:
        def score(self, query, contents):
            raise RuntimeError("reranker unavailable")

    pipeline = RerankingPipeline(BrokenProvider())

    with pytest.raises(
        RerankingError,
        match="reranker unavailable",
    ):
        pipeline.rerank(
            "test query",
            candidates,
        )
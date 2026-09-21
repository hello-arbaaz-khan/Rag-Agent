import math

import pytest
from pydantic import ValidationError

from RagCore.ErrorsHandle.exceptions import RetrievalError
from RagCore.Retrieval.pipeline import RetrievalPipeline
from RagCore.Retrieval.retrieval import RetrievalConfig, RetrievalResult


class FakeRepository:
    def __init__(self, results=None):
        self.results = results or []
        self.calls = []

    def search(self, query_embedding, top_k, document_ids=None):
        self.calls.append((query_embedding, top_k, document_ids))
        return self.results[:top_k]


def make_result(chunk_id, document_id, score, chunk_index):
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        content=f"content-{chunk_id}",
        score=score,
        chunk_index=chunk_index,
    )


def test_retrieval_config_defaults():
    config = RetrievalConfig()

    assert config.top_k == 20
    assert config.dimensions == 384


def test_retrieval_config_rejects_invalid_values():
    with pytest.raises(ValidationError):
        RetrievalConfig(top_k=0)

    with pytest.raises(ValidationError):
        RetrievalConfig(dimensions=0)


def test_retrieve_uses_default_top_k_20():
    repository = FakeRepository()
    pipeline = RetrievalPipeline(repository)

    pipeline.retrieve([0.0] * 384)

    assert repository.calls[0][1] == 20


def test_retrieve_respects_custom_top_k():
    repository = FakeRepository([
        make_result("1", "doc-1", 0.95, 0),
        make_result("2", "doc-1", 0.90, 1),
        make_result("3", "doc-1", 0.85, 2),
    ])
    pipeline = RetrievalPipeline(repository)

    results = pipeline.retrieve(
        [0.0] * 384,
        top_k=2,
    )

    assert len(results) == 2
    assert [result.chunk_id for result in results] == ["1", "2"]


def test_retrieve_empty_repository_returns_empty_list():
    repository = FakeRepository()
    pipeline = RetrievalPipeline(repository)

    results = pipeline.retrieve([0.0] * 384)

    assert results == []


def test_retrieve_preserves_similarity_order():
    repository = FakeRepository([
        make_result("1", "doc-1", 0.95, 0),
        make_result("2", "doc-1", 0.90, 1),
        make_result("3", "doc-1", 0.80, 2),
    ])
    pipeline = RetrievalPipeline(repository)

    results = pipeline.retrieve(
        [0.0] * 384,
        top_k=3,
    )

    assert [result.score for result in results] == [
        0.95,
        0.90,
        0.80,
    ]


def test_retrieve_rejects_empty_embedding():
    pipeline = RetrievalPipeline(FakeRepository())

    with pytest.raises(RetrievalError):
        pipeline.retrieve([])


def test_retrieve_rejects_wrong_embedding_dimensions():
    pipeline = RetrievalPipeline(FakeRepository())

    with pytest.raises(RetrievalError):
        pipeline.retrieve([0.0] * 383)


def test_retrieve_rejects_non_numeric_embedding():
    pipeline = RetrievalPipeline(FakeRepository())

    with pytest.raises(RetrievalError):
        pipeline.retrieve(
            [0.0] * 383 + ["invalid"]
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
    pipeline = RetrievalPipeline(FakeRepository())

    with pytest.raises(RetrievalError):
        pipeline.retrieve(
            [0.0] * 383 + [value]
        )


def test_retrieve_rejects_invalid_top_k():
    pipeline = RetrievalPipeline(FakeRepository())

    with pytest.raises(RetrievalError):
        pipeline.retrieve(
            [0.0] * 384,
            top_k=0,
        )


def test_retrieve_rejects_negative_top_k():
    pipeline = RetrievalPipeline(FakeRepository())

    with pytest.raises(RetrievalError):
        pipeline.retrieve(
            [0.0] * 384,
            top_k=-1,
        )


def test_retrieve_rejects_invalid_document_filter():
    pipeline = RetrievalPipeline(FakeRepository())

    with pytest.raises(RetrievalError):
        pipeline.retrieve(
            [0.0] * 384,
            document_ids=["doc-1", ""],
        )


def test_retrieve_passes_document_filter():
    repository = FakeRepository([
        make_result("1", "doc-1", 0.95, 0),
    ])
    pipeline = RetrievalPipeline(repository)

    pipeline.retrieve(
        [0.0] * 384,
        document_ids=["doc-1"],
    )

    assert repository.calls[0][2] == ["doc-1"]


def test_retrieve_wraps_repository_error():

    class BrokenRepository:
        def search(
            self,
            query_embedding,
            top_k,
            document_ids=None,
        ):
            raise RuntimeError("database unavailable")

    pipeline = RetrievalPipeline(BrokenRepository())

    with pytest.raises(
        RetrievalError,
        match="database unavailable",
    ):
        pipeline.retrieve([0.0] * 384)

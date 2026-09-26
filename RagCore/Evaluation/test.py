import pytest
from pydantic import ValidationError

from RagCore.Context.context import Context
from RagCore.ErrorsHandle.exceptions import EvaluationError
from RagCore.Evaluation.dataset import (
    EvaluationDataset,
    EvaluationSample,
)
from RagCore.Evaluation.generation import (
    GenerationEvaluator,
)
from RagCore.Evaluation.report import (
    EvaluationReport,
)
from RagCore.Evaluation.retrieval import (
    RetrievalEvaluator,
    RetrievalMetrics,
)
from RagCore.Retrieval.retrieval import RetrievalResult


def make_result(
    chunk_id: str,
    score: float = 1.0,
) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="doc-1",
        content=f"content-{chunk_id}",
        score=score,
        chunk_index=0,
    )


def test_sample_requires_relevant_ids():
    with pytest.raises(ValidationError):
        EvaluationSample(
            query="question",
            relevant_chunk_ids=[],
        )


def test_sample_rejects_blank_relevant_id():
    with pytest.raises(ValidationError):
        EvaluationSample(
            query="question",
            relevant_chunk_ids=[""],
        )


def test_sample_strips_query():
    sample = EvaluationSample(
        query="  question  ",
        relevant_chunk_ids=["a"],
    )

    assert sample.query == "question"


def test_duplicate_relevant_ids_are_removed():
    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=[
            "a",
            "a",
            "b",
        ],
    )

    assert sample.relevant_chunk_ids == [
        "a",
        "b",
    ]


def test_empty_dataset_is_rejected():
    dataset = EvaluationDataset()

    with pytest.raises(ValueError):
        dataset.validate_non_empty()


def test_recall_perfect():
    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=[
            "a",
            "b",
        ],
    )

    results = [
        make_result("a"),
        make_result("b"),
    ]

    metrics = RetrievalEvaluator(
        ks=[2]
    ).evaluate(
        sample,
        results,
    )

    assert metrics["recall@2"] == 1.0


def test_precision_perfect():
    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=[
            "a",
            "b",
        ],
    )

    results = [
        make_result("a"),
        make_result("b"),
    ]

    metrics = RetrievalEvaluator(
        ks=[2]
    ).evaluate(
        sample,
        results,
    )

    assert metrics["precision@2"] == 1.0


def test_hit_rate_perfect():
    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=["a"],
    )

    results = [
        make_result("a"),
    ]

    metrics = RetrievalEvaluator(
        ks=[1]
    ).evaluate(
        sample,
        results,
    )

    assert metrics["hit_rate@1"] == 1.0


def test_zero_relevant_results():
    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=["a"],
    )

    results = [
        make_result("x"),
        make_result("y"),
    ]

    metrics = RetrievalEvaluator(
        ks=[2]
    ).evaluate(
        sample,
        results,
    )

    assert metrics["recall@2"] == 0.0
    assert metrics["precision@2"] == 0.0
    assert metrics["hit_rate@2"] == 0.0
    assert metrics["ndcg@2"] == 0.0
    assert metrics["mrr"] == 0.0


def test_empty_retrieved_results():
    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=["a"],
    )

    metrics = RetrievalEvaluator(
        ks=[1]
    ).evaluate(
        sample,
        [],
    )

    assert metrics["recall@1"] == 0.0
    assert metrics["precision@1"] == 0.0
    assert metrics["hit_rate@1"] == 0.0
    assert metrics["ndcg@1"] == 0.0
    assert metrics["mrr"] == 0.0


def test_partial_retrieval():
    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=[
            "a",
            "b",
        ],
    )

    results = [
        make_result("x"),
        make_result("b"),
        make_result("y"),
    ]

    metrics = RetrievalEvaluator(
        ks=[3]
    ).evaluate(
        sample,
        results,
    )

    assert metrics["recall@3"] == 0.5
    assert metrics["precision@3"] == pytest.approx(
        1 / 3
    )
    assert metrics["hit_rate@3"] == 1.0


def test_mrr_is_ranking_sensitive():
    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=["a"],
    )

    first = RetrievalEvaluator(
        ks=[3]
    ).evaluate(
        sample,
        [
            make_result("a"),
            make_result("x"),
            make_result("y"),
        ],
    )

    third = RetrievalEvaluator(
        ks=[3]
    ).evaluate(
        sample,
        [
            make_result("x"),
            make_result("y"),
            make_result("a"),
        ],
    )

    assert first["mrr"] == 1.0
    assert third["mrr"] == pytest.approx(
        1 / 3
    )


def test_ndcg_is_ranking_sensitive():
    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=[
            "a",
            "b",
        ],
    )

    first = RetrievalEvaluator(
        ks=[2]
    ).evaluate(
        sample,
        [
            make_result("a"),
            make_result("b"),
        ],
    )

    reversed_results = RetrievalEvaluator(
        ks=[2]
    ).evaluate(
        sample,
        [
            make_result("b"),
            make_result("a"),
        ],
    )

    assert first["ndcg@2"] == 1.0
    assert reversed_results["ndcg@2"] == 1.0


def test_duplicate_retrieved_ids_do_not_inflate_metrics():
    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=["a"],
    )

    results = [
        make_result("a"),
        make_result("a"),
        make_result("x"),
    ]

    metrics = RetrievalEvaluator(
        ks=[3]
    ).evaluate(
        sample,
        results,
    )

    assert metrics["recall@3"] == 1.0
    assert metrics["precision@3"] == 1 / 2


def test_invalid_k():
    with pytest.raises(EvaluationError):
        RetrievalMetrics.recall_at_k(
            {"a"},
            ["a"],
            0,
        )


def test_negative_k():
    with pytest.raises(EvaluationError):
        RetrievalMetrics.recall_at_k(
            {"a"},
            ["a"],
            -1,
        )


def test_evaluator_rejects_invalid_k():
    with pytest.raises(EvaluationError):
        RetrievalEvaluator(ks=[0])


def test_dataset_and_results_length_must_match():
    evaluator = RetrievalEvaluator(
        ks=[1]
    )

    sample = EvaluationSample(
        query="question",
        relevant_chunk_ids=["a"],
    )

    with pytest.raises(EvaluationError):
        evaluator.evaluate_dataset(
            [sample],
            [],
        )


def test_generation_evaluator_accepts_reference_free_metrics():
    class FakeJudge:
        def evaluate(self, **kwargs):
            return {
                "faithfulness": 1.0,
                "answer_relevance": 0.8,
            }

    evaluator = GenerationEvaluator(
        FakeJudge()
    )

    result = evaluator.evaluate(
        query="question",
        context=Context(
            text="context"
        ),
        answer="answer",
    )

    assert result == {
        "faithfulness": 1.0,
        "answer_relevance": 0.8,
    }


def test_generation_evaluator_accepts_reference_metrics():
    class FakeJudge:
        def evaluate(self, **kwargs):
            return {
                "faithfulness": 1.0,
                "answer_relevance": 0.8,
                "factual_correctness": 0.9,
            }

    evaluator = GenerationEvaluator(
        FakeJudge()
    )

    result = evaluator.evaluate(
        query="question",
        context=Context(
            text="context"
        ),
        answer="answer",
        reference_answer="reference",
    )

    assert result == {
        "faithfulness": 1.0,
        "answer_relevance": 0.8,
        "factual_correctness": 0.9,
    }


def test_factual_correctness_requires_reference():
    class FakeJudge:
        def evaluate(self, **kwargs):
            return {
                "factual_correctness": 0.9,
            }

    evaluator = GenerationEvaluator(
        FakeJudge()
    )

    with pytest.raises(EvaluationError):
        evaluator.evaluate(
            query="question",
            context=Context(
                text="context"
            ),
            answer="answer",
        )


def test_generation_rejects_empty_query():
    class FakeJudge:
        def evaluate(self, **kwargs):
            return {
                "faithfulness": 1.0,
            }

    evaluator = GenerationEvaluator(
        FakeJudge()
    )

    with pytest.raises(EvaluationError):
        evaluator.evaluate(
            query="",
            context=Context(
                text="context"
            ),
            answer="answer",
        )


def test_generation_rejects_empty_answer():
    class FakeJudge:
        def evaluate(self, **kwargs):
            return {
                "faithfulness": 1.0,
            }

    evaluator = GenerationEvaluator(
        FakeJudge()
    )

    with pytest.raises(EvaluationError):
        evaluator.evaluate(
            query="question",
            context=Context(
                text="context"
            ),
            answer="",
        )


def test_generation_judge_failure_is_wrapped():
    class BrokenJudge:
        def evaluate(self, **kwargs):
            raise RuntimeError(
                "judge unavailable"
            )

    evaluator = GenerationEvaluator(
        BrokenJudge()
    )

    with pytest.raises(
        EvaluationError,
        match="judge unavailable",
    ):
        evaluator.evaluate(
            query="question",
            context=Context(
                text="context"
            ),
            answer="answer",
        )


def test_generation_rejects_invalid_metric():
    class FakeJudge:
        def evaluate(self, **kwargs):
            return {
                "faithfulness": 2.0,
            }

    evaluator = GenerationEvaluator(
        FakeJudge()
    )

    with pytest.raises(EvaluationError):
        evaluator.evaluate(
            query="question",
            context=Context(
                text="context"
            ),
            answer="answer",
        )


def test_report_aggregates_multiple_samples():
    report = EvaluationReport()

    report.add({
        "recall@5": 1.0,
        "mrr": 1.0,
    })

    report.add({
        "recall@5": 0.0,
        "mrr": 0.5,
    })

    assert report.aggregate() == {
        "mrr": 0.75,
        "recall@5": 0.5,
    }

    assert report.sample_count == 2


def test_report_handles_missing_metric_in_sample():
    report = EvaluationReport()

    report.add({
        "recall@5": 1.0,
    })

    report.add({
        "recall@5": 0.5,
        "mrr": 1.0,
    })

    assert report.aggregate() == {
        "mrr": 1.0,
        "recall@5": 0.75,
    }


def test_empty_report_cannot_be_aggregated():
    with pytest.raises(EvaluationError):
        EvaluationReport().aggregate()


def test_report_rejects_empty_metrics():
    with pytest.raises(EvaluationError):
        EvaluationReport().add({})
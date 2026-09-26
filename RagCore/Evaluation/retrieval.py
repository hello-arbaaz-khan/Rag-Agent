import math
from statistics import mean

from RagCore.ErrorsHandle.exceptions import EvaluationError
from RagCore.Evaluation.dataset import EvaluationSample
from RagCore.Retrieval.retrieval import RetrievalResult


class RetrievalMetrics:
    @staticmethod
    def _validate_k(k: int) -> None:
        if not isinstance(k, int) or k <= 0:
            raise EvaluationError(
                "K must be a positive integer."
            )

    @staticmethod
    def _validate_relevant_ids(
        relevant_ids: set[str],
    ) -> None:
        if not relevant_ids:
            raise EvaluationError(
                "Relevant IDs cannot be empty."
            )

    @staticmethod
    def _validate_retrieved_ids(
        retrieved_ids: list[str],
    ) -> None:
        if not isinstance(retrieved_ids, list):
            raise EvaluationError(
                "Retrieved IDs must be a list."
            )

        if any(
            not isinstance(chunk_id, str)
            for chunk_id in retrieved_ids
        ):
            raise EvaluationError(
                "Retrieved IDs must contain strings."
            )

    @classmethod
    def recall_at_k(
        cls,
        relevant_ids: set[str],
        retrieved_ids: list[str],
        k: int,
    ) -> float:
        cls._validate_k(k)
        cls._validate_relevant_ids(relevant_ids)
        cls._validate_retrieved_ids(retrieved_ids)

        top_k = retrieved_ids[:k]

        relevant_retrieved = (
            set(top_k) & relevant_ids
        )

        return (
            len(relevant_retrieved)
            / len(relevant_ids)
        )

    @classmethod
    def precision_at_k(
        cls,
        relevant_ids: set[str],
        retrieved_ids: list[str],
        k: int,
    ) -> float:
        cls._validate_k(k)
        cls._validate_relevant_ids(relevant_ids)
        cls._validate_retrieved_ids(retrieved_ids)

        top_k = retrieved_ids[:k]

        if not top_k:
            return 0.0

        relevant_retrieved = (
            set(top_k) & relevant_ids
        )

        return (
            len(relevant_retrieved)
            / len(top_k)
        )

    @classmethod
    def hit_rate_at_k(
        cls,
        relevant_ids: set[str],
        retrieved_ids: list[str],
        k: int,
    ) -> float:
        cls._validate_k(k)
        cls._validate_relevant_ids(relevant_ids)
        cls._validate_retrieved_ids(retrieved_ids)

        top_k = retrieved_ids[:k]

        return float(
            bool(set(top_k) & relevant_ids)
        )

    @classmethod
    def mrr(
        cls,
        relevant_ids: set[str],
        retrieved_ids: list[str],
    ) -> float:
        cls._validate_relevant_ids(relevant_ids)
        cls._validate_retrieved_ids(retrieved_ids)

        for rank, chunk_id in enumerate(
            retrieved_ids,
            start=1,
        ):
            if chunk_id in relevant_ids:
                return 1.0 / rank

        return 0.0

    @classmethod
    def ndcg_at_k(
        cls,
        relevant_ids: set[str],
        retrieved_ids: list[str],
        k: int,
    ) -> float:
        cls._validate_k(k)
        cls._validate_relevant_ids(relevant_ids)
        cls._validate_retrieved_ids(retrieved_ids)

        top_k = retrieved_ids[:k]

        dcg = 0.0

        for rank, chunk_id in enumerate(
            top_k,
            start=1,
        ):
            if chunk_id in relevant_ids:
                dcg += 1.0 / math.log2(
                    rank + 1
                )

        ideal_count = min(
            len(relevant_ids),
            k,
        )

        if ideal_count == 0:
            return 0.0

        idcg = sum(
            1.0 / math.log2(rank + 1)
            for rank in range(1, ideal_count + 1)
        )

        return dcg / idcg


class RetrievalEvaluator:
    def __init__(
        self,
        ks: list[int] | None = None,
    ) -> None:
        self.ks = sorted(
            set(ks or [1, 3, 5, 10])
        )

        if not self.ks:
            raise EvaluationError(
                "At least one K value is required."
            )

        if any(k <= 0 for k in self.ks):
            raise EvaluationError(
                "K values must be greater than zero."
            )

    @staticmethod
    def _extract_ids(
        results: list[RetrievalResult],
    ) -> list[str]:
        if not isinstance(results, list):
            raise EvaluationError(
                "Retrieved results must be a list."
            )

        ids = []
        seen = set()

        for result in results:
            if not isinstance(
                result,
                RetrievalResult,
            ):
                raise EvaluationError(
                    "Retrieved results must contain "
                    "RetrievalResult objects."
                )

            if result.chunk_id in seen:
                continue

            ids.append(result.chunk_id)
            seen.add(result.chunk_id)

        return ids

    def evaluate(
        self,
        sample: EvaluationSample,
        retrieved_results: list[RetrievalResult],
    ) -> dict[str, float]:
        if not isinstance(
            sample,
            EvaluationSample,
        ):
            raise EvaluationError(
                "sample must be an EvaluationSample."
            )

        retrieved_ids = self._extract_ids(
            retrieved_results
        )

        relevant_ids = set(
            sample.relevant_chunk_ids
        )

        metrics = {
            "mrr": RetrievalMetrics.mrr(
                relevant_ids,
                retrieved_ids,
            ),
        }

        for k in self.ks:
            metrics[
                f"recall@{k}"
            ] = RetrievalMetrics.recall_at_k(
                relevant_ids,
                retrieved_ids,
                k,
            )

            metrics[
                f"precision@{k}"
            ] = RetrievalMetrics.precision_at_k(
                relevant_ids,
                retrieved_ids,
                k,
            )

            metrics[
                f"hit_rate@{k}"
            ] = RetrievalMetrics.hit_rate_at_k(
                relevant_ids,
                retrieved_ids,
                k,
            )

            metrics[
                f"ndcg@{k}"
            ] = RetrievalMetrics.ndcg_at_k(
                relevant_ids,
                retrieved_ids,
                k,
            )

        return metrics

    def evaluate_dataset(
        self,
        dataset: list[EvaluationSample],
        results: list[list[RetrievalResult]],
    ) -> dict[str, float]:
        if not dataset:
            raise EvaluationError(
                "Evaluation dataset cannot be empty."
            )

        if len(dataset) != len(results):
            raise EvaluationError(
                "Dataset and results must have "
                "the same length."
            )

        sample_metrics = [
            self.evaluate(
                sample,
                retrieved,
            )
            for sample, retrieved in zip(
                dataset,
                results,
            )
        ]

        metric_names = sample_metrics[0].keys()

        return {
            name: mean(
                metrics[name]
                for metrics in sample_metrics
            )
            for name in metric_names
        }
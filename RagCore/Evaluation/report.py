from statistics import mean
from typing import Any

from RagCore.ErrorsHandle.exceptions import EvaluationError


class EvaluationReport:
    def __init__(self) -> None:
        self.samples: list[dict[str, float]] = []

    def add(
        self,
        metrics: dict[str, float],
    ) -> None:
        if not isinstance(
            metrics,
            dict,
        ) or not metrics:
            raise EvaluationError(
                "Evaluation metrics must be "
                "a non-empty dictionary."
            )

        normalized = {}

        for name, value in metrics.items():
            if not isinstance(
                name,
                str,
            ) or not name.strip():
                raise EvaluationError(
                    "Metric names must be "
                    "non-empty strings."
                )

            try:
                numeric_value = float(value)
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise EvaluationError(
                    f"Metric '{name}' must be numeric."
                ) from exc

            normalized[name] = numeric_value

        self.samples.append(normalized)

    def aggregate(self) -> dict[str, float]:
        if not self.samples:
            raise EvaluationError(
                "Cannot aggregate an empty "
                "evaluation report."
            )

        metric_names = set()

        for sample in self.samples:
            metric_names.update(
                sample.keys()
            )

        aggregated = {}

        for name in sorted(metric_names):
            values = [
                sample[name]
                for sample in self.samples
                if name in sample
            ]

            aggregated[name] = mean(values)

        return aggregated

    @property
    def sample_count(self) -> int:
        return len(self.samples)
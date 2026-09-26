from typing import Protocol

from RagCore.Context.context import Context
from RagCore.ErrorsHandle.exceptions import EvaluationError


class GenerationJudge(Protocol):
    def evaluate(
        self,
        *,
        query: str,
        context: str,
        answer: str,
        reference_answer: str | None = None,
    ) -> dict[str, float]:
        ...


class GenerationEvaluator:
    REFERENCE_REQUIRED_METRICS = {
        "factual_correctness",
    }

    def __init__(
        self,
        judge: GenerationJudge,
    ) -> None:
        self.judge = judge

    def evaluate(
        self,
        *,
        query: str,
        context: Context,
        answer: str,
        reference_answer: str | None = None,
    ) -> dict[str, float]:
        if not isinstance(
            query,
            str,
        ) or not query.strip():
            raise EvaluationError(
                "Evaluation query must be non-empty."
            )

        if not isinstance(
            context,
            Context,
        ):
            raise EvaluationError(
                "Context must be a Context object."
            )

        if not isinstance(
            answer,
            str,
        ) or not answer.strip():
            raise EvaluationError(
                "Evaluation answer must be non-empty."
            )

        if reference_answer is not None:
            if not isinstance(
                reference_answer,
                str,
            ):
                raise EvaluationError(
                    "Reference answer must be a string or None."
                )

            reference_answer = (
                reference_answer.strip()
            )

            if not reference_answer:
                reference_answer = None

        try:
            metrics = self.judge.evaluate(
                query=query.strip(),
                context=context.text,
                answer=answer.strip(),
                reference_answer=reference_answer,
            )
        except EvaluationError:
            raise
        except Exception as exc:
            raise EvaluationError(
                str(exc)
            ) from exc

        if not isinstance(
            metrics,
            dict,
        ):
            raise EvaluationError(
                "Generation judge must return "
                "a metric dictionary."
            )

        if not metrics:
            raise EvaluationError(
                "Generation judge returned no metrics."
            )

        normalized = {}

        for name, value in metrics.items():
            if not isinstance(
                name,
                str,
            ) or not name.strip():
                raise EvaluationError(
                    "Generation metric names "
                    "must be non-empty strings."
                )

            try:
                numeric_value = float(value)
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise EvaluationError(
                    f"Generation metric '{name}' "
                    "must be numeric."
                ) from exc

            if not 0.0 <= numeric_value <= 1.0:
                raise EvaluationError(
                    f"Generation metric '{name}' "
                    "must be between 0 and 1."
                )

            normalized[name] = numeric_value

        if (
            "factual_correctness" in normalized
            and reference_answer is None
        ):
            raise EvaluationError(
                "Factual correctness requires "
                "a reference answer."
            )

        return normalized
from typing import Any

from RagCore.ErrorsHandle.exceptions import EvaluationError
from RagCore.Generation.provider import GenerationProvider


class LLMGenerationJudge:
    """
    Uses a real LLM generation provider to evaluate
    a generated RAG answer against its retrieved context.

    The judge returns normalized scores in the range [0, 1].
    """

    SYSTEM_PROMPT = """
You are an evaluation judge for a Retrieval-Augmented Generation system.

Evaluate the answer using ONLY the provided context.

Return a JSON object containing exactly these numeric fields:

{
    "faithfulness": 0.0,
    "answer_relevance": 0.0,
    "factual_correctness": 0.0
}

Scoring:

faithfulness:
- 1.0 = every important claim in the answer is supported by the context.
- 0.0 = the answer is unsupported by the context.
- Use values between 0 and 1 when partially supported.

answer_relevance:
- 1.0 = directly and completely answers the question.
- 0.0 = does not answer the question.
- Use values between 0 and 1 when partially relevant.

factual_correctness:
- Compare the answer against the reference answer.
- 1.0 = factually equivalent.
- 0.0 = factually incorrect.
- Use values between 0 and 1 when partially correct.

Return JSON only.
Do not include markdown.
Do not include explanations outside the JSON.
""".strip()

    def __init__(
        self,
        provider: GenerationProvider,
    ) -> None:
        self.provider = provider

    def evaluate(
        self,
        *,
        query: str,
        context: str,
        answer: str,
        reference_answer: str | None = None,
    ) -> dict[str, float]:
        if not query.strip():
            raise EvaluationError(
                "Evaluation query must be non-empty."
            )

        if not context.strip():
            raise EvaluationError(
                "Evaluation context must be non-empty."
            )

        if not answer.strip():
            raise EvaluationError(
                "Evaluation answer must be non-empty."
            )

        if not reference_answer or not reference_answer.strip():
            raise EvaluationError(
                "Reference answer is required for LLM generation evaluation."
            )

        user_prompt = self._build_prompt(
            query=query,
            context=context,
            answer=answer,
            reference_answer=reference_answer,
        )

        try:
            raw_response = self.provider.generate(
                self.SYSTEM_PROMPT,
                user_prompt,
            )
        except Exception as exc:
            raise EvaluationError(
                f"Generation judge failed: {exc}"
            ) from exc

        return self._parse_response(raw_response)

    def _build_prompt(
        self,
        *,
        query: str,
        context: str,
        answer: str,
        reference_answer: str,
    ) -> str:
        return (
            f"Question:\n"
            f"{query.strip()}\n\n"
            f"Context:\n"
            f"{context.strip()}\n\n"
            f"Generated answer:\n"
            f"{answer.strip()}\n\n"
            f"Reference answer:\n"
            f"{reference_answer.strip()}"
        )

    def _parse_response(
        self,
        response: str,
    ) -> dict[str, float]:
        if not isinstance(response, str) or not response.strip():
            raise EvaluationError(
                "Generation judge returned an empty response."
            )

        try:
            import json

            data: Any = json.loads(response)
        except (json.JSONDecodeError, TypeError) as exc:
            raise EvaluationError(
                "Generation judge returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise EvaluationError(
                "Generation judge response must be a JSON object."
            )

        required_metrics = {
            "faithfulness",
            "answer_relevance",
            "factual_correctness",
        }

        if set(data.keys()) != required_metrics:
            raise EvaluationError(
                "Generation judge must return exactly: "
                "faithfulness, answer_relevance, "
                "factual_correctness."
            )

        normalized: dict[str, float] = {}

        for name in required_metrics:
            value = data[name]

            try:
                numeric_value = float(value)
            except (TypeError, ValueError) as exc:
                raise EvaluationError(
                    f"Generation metric '{name}' must be numeric."
                ) from exc

            if not 0.0 <= numeric_value <= 1.0:
                raise EvaluationError(
                    f"Generation metric '{name}' must be between 0 and 1."
                )

            normalized[name] = numeric_value

        return normalized
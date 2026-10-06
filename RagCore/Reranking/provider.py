from typing import Protocol

from sentence_transformers import CrossEncoder


class RerankerProvider(Protocol):
    def score(
        self,
        query: str,
        contents: list[str],
    ) -> list[float]:
        ...


class PassthroughRerankerProvider:
    """
    Deterministic no-op provider.

    Keep this available for isolated tests.
    Production chat should use CrossEncoderRerankerProvider.
    """

    def score(
        self,
        query: str,
        contents: list[str],
    ) -> list[float]:
        return [1.0] * len(contents)


class CrossEncoderRerankerProvider:
    """
    Production reranker.

    Scores each query/chunk pair jointly instead of relying only
    on embedding similarity.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ) -> None:
        self.model_name = model_name
        self._model: CrossEncoder | None = None

    def _get_model(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(
                self.model_name
            )

        return self._model

    def score(
        self,
        query: str,
        contents: list[str],
    ) -> list[float]:
        if not contents:
            return []

        pairs = [
            [query, content]
            for content in contents
        ]

        scores = self._get_model().predict(pairs)

        return [
            float(score)
            for score in scores
        ]
from RagCore.ErrorsHandle.exceptions import RerankingError
from RagCore.Retrieval.retrieval import RetrievalResult

from RagCore.Reranking.reranking import RerankingConfig
from RagCore.Reranking.provider import RerankerProvider

class RerankingPipeline:
    def __init__(self,provider: RerankerProvider,config: RerankingConfig | None = None) -> None:
        self.provider = provider
        self.config = config or RerankingConfig()

    def rerank(self,query: str,candidates: list[RetrievalResult],*,top_k: int | None = None) -> list[RetrievalResult]:

        requested_top_k = (
            self.config.top_k
            if top_k is None
            else top_k
        )

        if requested_top_k <= 0:
            raise RerankingError(
                "top_k must be greater than zero."
            )

        if not isinstance(query, str) or not query.strip():
            raise RerankingError(
                "Query must be a non-empty string."
            )

        if not isinstance(candidates, list):
            raise RerankingError(
                "Candidates must be a list."
            )

        if not candidates:
            return []

        if any(
            not isinstance(candidate, RetrievalResult)
            for candidate in candidates
        ):
            raise RerankingError(
                "Candidates must contain RetrievalResult objects."
            )

        contents = [
            candidate.content
            for candidate in candidates
        ]

        if any(
            not isinstance(content, str) or not content.strip()
            for content in contents
        ):
            raise RerankingError(
                "Candidate content must be non-empty strings."
            )

        try:
            scores = self.provider.score(
                query.strip(),
                contents,
            )
        except Exception as exc:
            raise RerankingError(str(exc)) from exc

        if len(scores) != len(candidates):
            raise RerankingError(
                "Reranker provider returned a different number "
                "of scores than candidates."
            )

        scored_candidates = []

        for candidate, score in zip(candidates, scores):
            try:
                rerank_score = float(score)
            except (TypeError, ValueError) as exc:
                raise RerankingError(
                    "Reranker scores must be numeric."
                ) from exc

            metadata = dict(candidate.metadata)
            metadata["rerank_score"] = rerank_score

            scored_candidates.append(
                candidate.model_copy(
                    update={
                        "metadata": metadata,
                    }
                )
            )

        scored_candidates.sort(
            key=lambda candidate: candidate.metadata["rerank_score"],
            reverse=True,
        )

        return scored_candidates[:requested_top_k]
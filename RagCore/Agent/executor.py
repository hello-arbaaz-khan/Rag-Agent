import re

from RagCore.Agent.state import AgentState
from RagCore.Agent.tools import DocumentSearchTool
from RagCore.ErrorsHandle.exceptions import AgentError
from RagCore.Retrieval.retrieval import RetrievalResult


class AgentExecutor:
    def __init__(
        self,
        search_tool: DocumentSearchTool,
        max_steps: int = 5,
        retrieval_top_k: int = 20,
        reranking_top_k: int = 5,
    ) -> None:
        self.search_tool = search_tool
        self.max_steps = max_steps
        self.retrieval_top_k = retrieval_top_k
        self.reranking_top_k = reranking_top_k

    def execute(
        self,
        queries: list[str],
        state: AgentState,
    ) -> list[RetrievalResult]:
        if not queries:
            raise AgentError(
                "Executor received no queries."
            )

        if len(queries) > self.max_steps:
            raise AgentError(
                "Agent exceeded maximum execution steps."
            )

        all_candidates: list[RetrievalResult] = []

        for query in queries:
            results = self.search_tool.search(
                query,
                document_ids=state.document_ids,
                retrieval_top_k=self.retrieval_top_k,
                reranking_top_k=self.reranking_top_k,
            )

            state.retrieval_attempts += 1
            state.completed_queries.append(query)

            all_candidates.extend(results)

        state.candidates_count = len(all_candidates)

        return self._deduplicate(all_candidates)

    @staticmethod
    def _normalize_content(
        content: str,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            content,
        ).strip().casefold()

    @classmethod
    def _deduplicate(
        cls,
        candidates: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        unique_by_id: dict[
            str,
            RetrievalResult,
        ] = {}

        seen_content: set[str] = set()

        for candidate in candidates:
            if candidate.chunk_id in unique_by_id:
                continue

            normalized_content = cls._normalize_content(
                candidate.content
            )

            if not normalized_content:
                continue

            if normalized_content in seen_content:
                continue

            unique_by_id[
                candidate.chunk_id
            ] = candidate

            seen_content.add(
                normalized_content
            )

        return list(
            unique_by_id.values()
        )
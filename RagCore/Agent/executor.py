from RagCore.Agent.state import AgentState
from RagCore.Agent.tools import DocumentSearchTool
from RagCore.ErrorsHandle.exceptions import AgentError
from RagCore.Retrieval.retrieval import RetrievalResult


class AgentExecutor:
    def __init__(
        self,
        search_tool: DocumentSearchTool,
        max_steps: int = 5,
    ) -> None:
        self.search_tool = search_tool
        self.max_steps = max_steps

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
            )

            state.retrieval_attempts += 1
            state.completed_queries.append(query)

            all_candidates.extend(results)

        state.candidates_count = len(all_candidates)

        return self._deduplicate(all_candidates)

    @staticmethod
    def _deduplicate(
        candidates: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        unique: dict[str, RetrievalResult] = {}

        for candidate in candidates:
            unique[candidate.chunk_id] = candidate

        return list(unique.values())
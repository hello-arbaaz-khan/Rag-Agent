import json
from dataclasses import dataclass

from RagCore.ErrorsHandle.exceptions import AgentError


@dataclass(frozen=True)
class AgentPlan:
    queries: list[str]

    @property
    def is_multi_step(self) -> bool:
        return len(self.queries) > 1


class PlannerProvider:
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        raise NotImplementedError


class AgentPlanner:
    SYSTEM_PROMPT = """
You are the planning component of a document question-answering system.

Your job is to decide how many document searches are needed.

Rules:
- For a simple question, return one query.
- For a comparison, commonality, difference, aggregation,
  or multi-document question, create focused subqueries.
- Each subquery must be independently understandable.
- Do not answer the user's question.
- Do not invent document information.
- Return ONLY valid JSON.

Required format:
{
  "queries": [
    "query 1",
    "query 2"
  ]
}
""".strip()

    def __init__(
        self,
        provider: PlannerProvider,
        max_subqueries: int = 5,
    ) -> None:
        self.provider = provider
        self.max_subqueries = max_subqueries

    def plan(
        self,
        question: str,
        *,
        conversation_context: str = "",
    ) -> AgentPlan:
        if not isinstance(question, str) or not question.strip():
            raise AgentError(
                "Planner question must be a non-empty string."
            )

        prompt = (
            f"Conversation context:\n"
            f"{conversation_context}\n\n"
            f"User question:\n"
            f"{question.strip()}"
        )

        try:
            response = self.provider.generate(
                self.SYSTEM_PROMPT,
                prompt,
            )
        except Exception as exc:
            raise AgentError(
                str(exc)
            ) from exc

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise AgentError(
                "Planner returned invalid JSON."
            ) from exc

        queries = data.get("queries")

        if not isinstance(queries, list):
            raise AgentError(
                "Planner response must contain a queries list."
            )

        cleaned_queries = [
            query.strip()
            for query in queries
            if isinstance(query, str) and query.strip()
        ]

        if not cleaned_queries:
            raise AgentError(
                "Planner returned no usable queries."
            )

        cleaned_queries = cleaned_queries[:self.max_subqueries]

        return AgentPlan(
            queries=cleaned_queries,
        )
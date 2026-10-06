import json
import re
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

1. For a simple factual question, return exactly ONE focused query.

2. For a question asking whether the document contains information
   about a person, place, country, topic, subject, or entity,
   return exactly ONE query containing the important subject.

3. For overview questions such as:
   - "what information is in this document?"
   - "what does this document contain?"
   - "what topics are covered?"
   - "tell me about this document"

   return exactly ONE broad query. Do not create generic
   subqueries such as "what information" or "what is in document".

4. Only use multiple queries when the question genuinely requires:
   - comparison
   - differences
   - commonality
   - aggregation
   - multiple independent subjects
   - multiple documents

5. Every query must be independently understandable.

6. Do not answer the user's question.

7. Do not invent document information.

8. Return ONLY valid JSON.

Required format:

{
  "queries": [
    "query 1"
  ]
}
""".strip()

    _MULTI_QUERY_PATTERNS = (
        r"\bcompare\b",
        r"\bcomparison\b",
        r"\bcompare\s+and\b",
        r"\bdifference(?:s)?\b",
        r"\bdifferent\b",
        r"\bsimilar(?:ity|ities)?\b",
        r"\bcommon\b",
        r"\bbetween\b",
        r"\bversus\b",
        r"\bvs\.?\b",
        r"\bboth\b",
        r"\beach\b",
        r"\ball\s+of\b",
    )

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

        normalized_question = question.strip()

        # ---------------------------------------------------------
        # Simple questions should NOT be sent to the LLM planner.
        #
        # This prevents questions such as:
        # "have you any information about Pakistan"
        #
        # from becoming several noisy searches.
        # ---------------------------------------------------------

        if not self._requires_multiple_queries(
            normalized_question
        ):
            return AgentPlan(
                queries=[
                    normalized_question
                ]
            )

        prompt = (
            f"Conversation context:\n"
            f"{conversation_context}\n\n"
            f"User question:\n"
            f"{normalized_question}"
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

        response_text = response.strip()

        if response_text.startswith("```"):
            lines = response_text.splitlines()

            if (
                lines
                and lines[0].startswith("```")
            ):
                lines = lines[1:]

            if (
                lines
                and lines[-1].startswith("```")
            ):
                lines = lines[:-1]

            response_text = "\n".join(
                lines
            ).strip()

        try:
            data = json.loads(response_text)

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
            if isinstance(query, str)
            and query.strip()
        ]

        if not cleaned_queries:
            raise AgentError(
                "Planner returned no usable queries."
            )

        cleaned_queries = list(
            dict.fromkeys(
                cleaned_queries
            )
        )

        cleaned_queries = cleaned_queries[
            :self.max_subqueries
        ]

        return AgentPlan(
            queries=cleaned_queries
        )

    @classmethod
    def _requires_multiple_queries(
        cls,
        question: str,
    ) -> bool:

        normalized = question.lower().strip()

        return any(
            re.search(
                pattern,
                normalized,
            )
            for pattern in cls._MULTI_QUERY_PATTERNS
        )
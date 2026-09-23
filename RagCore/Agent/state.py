from dataclasses import dataclass, field


@dataclass
class AgentState:
    question: str
    document_ids: list[str] | None = None
    conversation_context: str = ""

    subqueries: list[str] = field(default_factory=list)
    completed_queries: list[str] = field(default_factory=list)

    retrieval_attempts: int = 0
    candidates_count: int = 0

    final_answer: str | None = None
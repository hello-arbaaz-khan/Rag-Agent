from pydantic import BaseModel, Field

from RagCore.Agent.executor import AgentExecutor
from RagCore.Agent.planner import AgentPlanner
from RagCore.Agent.state import AgentState
from RagCore.Context.builder import ContextBuilder
from RagCore.ErrorsHandle.exceptions import AgentError
from RagCore.Generation.pipeline import GenerationPipeline
from RagCore.Query.query import Query


class AgentConfig(BaseModel):
    retrieval_top_k: int = Field(
        default=20,
        gt=0,
    )

    reranking_top_k: int = Field(
        default=5,
        gt=0,
    )

    max_steps: int = Field(
        default=5,
        gt=0,
    )

    max_subqueries: int = Field(
        default=5,
        gt=0,
    )


class Agent:
    def __init__(
        self,
        planner: AgentPlanner,
        executor: AgentExecutor,
        context_builder: ContextBuilder,
        generation_pipeline: GenerationPipeline,
        config: AgentConfig | None = None,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.context_builder = context_builder
        self.generation_pipeline = generation_pipeline
        self.config = config or AgentConfig()

    def run(
        self,
        question: str,
        *,
        document_ids: list[str] | None = None,
        conversation_context: str = "",
    ) -> str:
        if not isinstance(question, str) or not question.strip():
            raise AgentError(
                "Question must be a non-empty string."
            )

        state = AgentState(
            question=question.strip(),
            document_ids=document_ids,
            conversation_context=conversation_context,
        )

        try:
            plan = self.planner.plan(
                state.question,
                conversation_context=state.conversation_context,
            )

            state.subqueries = plan.queries

            candidates = self.executor.execute(
                plan.queries,
                state,
            )

            context = self.context_builder.build(
                candidates,
            )

            query = Query(
                text=state.question,
            )

            answer = self.generation_pipeline.generate(
                query,
                context,
            )

            state.final_answer = answer

            return answer

        except AgentError:
            raise
        except Exception as exc:
            raise AgentError(
                str(exc)
            ) from exc
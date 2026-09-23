from RagCore.Context.context import Context
from RagCore.ErrorsHandle.exceptions import GenerationError
from RagCore.Query.query import Query

from RagCore.Generation.generation import GenerationConfig
from RagCore.Generation.provider import GenerationProvider


class GenerationPipeline:
    SYSTEM_PROMPT = (
        "You are a helpful RAG assistant. "
        "Answer the user's question using only the provided context. "
        "If the context does not contain enough information to answer, "
        "say that the available context does not contain enough information. "
        "Do not invent facts that are not supported by the context."
    )

    def __init__(self,provider: GenerationProvider,config: GenerationConfig | None = None) -> None:
        self.provider = provider
        self.config = config or GenerationConfig()

    def generate(self,query: Query,context: Context) -> str:
        if not isinstance(query, Query):
            raise GenerationError(
                "Query must be a Query object."
            )

        if not isinstance(context, Context):
            raise GenerationError(
                "Context must be a Context object."
            )

        user_prompt = self._build_prompt(
            query,
            context,
        )

        try:
            answer = self.provider.generate(
                self.SYSTEM_PROMPT,
                user_prompt,
            )
        except GenerationError:
            raise
        except Exception as exc:
            raise GenerationError(str(exc)) from exc

        if not isinstance(answer, str) or not answer.strip():
            raise GenerationError(
                "Generation provider returned an empty response."
            )

        return answer.strip()

    def _build_prompt(self,query: Query,context: Context) -> str:
        return (
            f"Context:\n"
            f"{context.text}\n\n"
            f"Question:\n"
            f"{query.normalize_text()}"
        )
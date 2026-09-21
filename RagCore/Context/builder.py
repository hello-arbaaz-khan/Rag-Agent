from RagCore.Retrieval.retrieval import RetrievalResult
from RagCore.Context.context import Context, ContextConfig


class ContextBuilder:
    def __init__(self,config: ContextConfig | None = None) -> None:
        self.config = config or ContextConfig()

    def build(self,candidates: list[RetrievalResult]) -> Context:
        candidates = candidates[:self.config.max_chunks]

        if not candidates:
            return Context(text="", sources=[])

        sections = []
        sources = []

        for candidate in candidates:
            sections.append(candidate.content)

            sources.append(
                {
                    "chunk_id": candidate.chunk_id,
                    "document_id": candidate.document_id,
                    "page_number": candidate.page_number,
                    "chunk_index": candidate.chunk_index,
                    "metadata": candidate.metadata,
                }
            )

        return Context(
            text=self.config.separator.join(sections),
            sources=sources,
        )
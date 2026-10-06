import re

from RagCore.Context.context import (
    Context,
    ContextConfig,
)
from RagCore.Retrieval.retrieval import (
    RetrievalResult,
)


class ContextBuilder:
    def __init__(
        self,
        config: ContextConfig | None = None,
    ) -> None:
        self.config = (
            config
            or ContextConfig()
        )

    @staticmethod
    def _normalize_content(
        content: str,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            content,
        ).strip().casefold()

    def build(
        self,
        candidates: list[RetrievalResult],
    ) -> Context:

        if not candidates:
            return Context(
                text="",
                sources=[],
            )

        sections: list[str] = []
        sources: list[dict] = []

        seen_content: set[str] = set()

        for candidate in candidates:

            normalized_content = (
                self._normalize_content(
                    candidate.content
                )
            )

            if not normalized_content:
                continue

            if normalized_content in seen_content:
                continue

            seen_content.add(
                normalized_content
            )

            source_number = (
                len(sections) + 1
            )

            page = (
                str(candidate.page_number)
                if candidate.page_number is not None
                else "unknown"
            )

            section = "\n".join(
                [
                    f"[Source {source_number}]",
                    f"Document ID: {candidate.document_id}",
                    f"Page: {page}",
                    f"Chunk: {candidate.chunk_index}",
                    "Content:",
                    candidate.content.strip(),
                ]
            )

            sections.append(section)

            sources.append(
                {
                    "source_number": source_number,
                    "chunk_id": candidate.chunk_id,
                    "document_id": candidate.document_id,
                    "page_number": candidate.page_number,
                    "chunk_index": candidate.chunk_index,
                    "score": candidate.score,
                    "rerank_score": candidate.metadata.get(
                        "rerank_score"
                    ),
                    "metadata": candidate.metadata,
                }
            )

            if (
                len(sections)
                >= self.config.max_chunks
            ):
                break

        if not sections:
            return Context(
                text="",
                sources=[],
            )

        return Context(
            text=self.config.separator.join(
                sections
            ),
            sources=sources,
        )
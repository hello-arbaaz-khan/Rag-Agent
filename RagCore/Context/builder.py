import re

from RagCore.Context.context import Context, ContextConfig
from RagCore.Retrieval.retrieval import RetrievalResult


class ContextBuilder:
    def __init__(
        self,
        config: ContextConfig | None = None,
    ) -> None:
        self.config = config or ContextConfig()

    @staticmethod
    def _normalize_content(content: str) -> str:
        return re.sub(r"\s+", " ", content).strip().casefold()

    @staticmethod
    def _document_label(candidate: RetrievalResult) -> str:
        metadata = candidate.metadata or {}

        for key in (
            "document_name",
            "document_title",
            "filename",
            "file_name",
            "title",
            "name",
        ):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        return str(candidate.document_id)

    def _select_candidates(
        self,
        candidates: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        limit = self.config.max_chunks
        selected: list[RetrievalResult] = []
        selected_ids: set[str] = set()
        seen_content: set[str] = set()

        # First pass: represent each document that has retrieved evidence.
        # This improves coverage without fabricating missing evidence.
        represented_documents: set[str] = set()

        for candidate in candidates:
            normalized = self._normalize_content(candidate.content)

            if not normalized or normalized in seen_content:
                continue

            document_id = str(candidate.document_id)

            if document_id in represented_documents:
                continue

            selected.append(candidate)
            selected_ids.add(candidate.chunk_id)
            seen_content.add(normalized)
            represented_documents.add(document_id)

            if len(selected) >= limit:
                return selected

        # Second pass: fill remaining slots with other relevant excerpts.
        for candidate in candidates:
            if candidate.chunk_id in selected_ids:
                continue

            normalized = self._normalize_content(candidate.content)

            if not normalized or normalized in seen_content:
                continue

            selected.append(candidate)
            selected_ids.add(candidate.chunk_id)
            seen_content.add(normalized)

            if len(selected) >= limit:
                break

        return selected

    def build(
        self,
        candidates: list[RetrievalResult],
    ) -> Context:
        if not candidates:
            return Context(text="", sources=[])

        selected = self._select_candidates(candidates)

        sections: list[str] = []
        sources: list[dict] = []

        for source_number, candidate in enumerate(selected, start=1):
            document_label = self._document_label(candidate)

            page = (
                str(candidate.page_number)
                if candidate.page_number is not None
                else "unavailable"
            )

            section = "\n".join(
                [
                    f"[Source {source_number}]",
                    f"Document: {document_label}",
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
                    "document_name": document_label,
                    "page_number": candidate.page_number,
                    "chunk_index": candidate.chunk_index,
                    "score": candidate.score,
                    "rerank_score": candidate.metadata.get(
                        "rerank_score"
                    ),
                    "metadata": candidate.metadata,
                }
            )

        return Context(
            text=self.config.separator.join(sections),
            sources=sources,
        )
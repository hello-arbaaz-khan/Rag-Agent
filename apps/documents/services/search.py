import re
from dataclasses import dataclass
from functools import lru_cache

from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
)
from django.db.models import F, QuerySet

from apps.documents.models import (
    DocumemtsChunk,
    UploadedDocument,
)

from apps.documents.Retrieval.pgvector_retriever import (
    DjangoPgVectorRepository,
)

from RagCore.Embeddings.embedding import (
    EmbeddingConfig,
)

from RagCore.Embeddings.provider import (
    EmbeddingProvider,
    SentenceTransformerProvider,
)


MIN_RELEVANCE = 0.48


_QUERY_STOP_WORDS = {
    "a",
    "about",
    "and",
    "are",
    "document",
    "documents",
    "end",
    "file",
    "files",
    "find",
    "for",
    "give",
    "have",
    "info",
    "information",
    "me",
    "name",
    "of",
    "that",
    "the",
    "to",
    "which",
    "with",
}


@dataclass(frozen=True)
class DocumentSearchMatch:
    document_id: int
    relevance_score: float
    matched_snippet: str | None


class DocumentSearchService:

    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        vector_repository: (
            DjangoPgVectorRepository | None
        ) = None,
    ) -> None:

        self.embedding_provider = (
            embedding_provider
        )

        self.vector_repository = (
            vector_repository
            or DjangoPgVectorRepository(
                DocumemtsChunk
            )
        )

    def search(
        self,
        query: str,
        *,
        user_id: int,
        documents: QuerySet[UploadedDocument],
        top_k: int,
    ) -> list[DocumentSearchMatch]:

        query = query.strip()

        eligible_documents = (
            documents.filter(
                user_id=user_id,
                is_processed=True,
                chunks__chunks_text__gt="",
            )
            .distinct()
        )

        eligible_ids = list(
            eligible_documents.values_list(
                "id",
                flat=True,
            )
        )

        if not eligible_ids:
            return []

        # -------------------------------------------------
        # Exact filename search
        # -------------------------------------------------

        requested_filename = (
            _extract_requested_filename(
                query
            )
        )

        if requested_filename:

            exact_documents = (
                eligible_documents.filter(
                    name__iexact=requested_filename
                )
            )

            exact_ids = list(
                exact_documents.values_list(
                    "id",
                    flat=True,
                )
            )

            if exact_ids:
                return [
                    DocumentSearchMatch(
                        document_id=document_id,
                        relevance_score=1.0,
                        matched_snippet=None,
                    )
                    for document_id in exact_ids[:top_k]
                ]

            return []

        # -------------------------------------------------
        # File type / extension search
        # -------------------------------------------------

        requested_file_type = (
            _extract_requested_file_type(
                query
            )
        )

        if requested_file_type:

            type_documents = (
                eligible_documents.filter(
                    file_type__iexact=(
                        requested_file_type
                    )
                )
                .order_by(
                    "name",
                    "id",
                )
            )

            return [
                DocumentSearchMatch(
                    document_id=document_id,
                    relevance_score=1.0,
                    matched_snippet=None,
                )
                for document_id in (
                    type_documents.values_list(
                        "id",
                        flat=True,
                    )[:top_k]
                )
            ]

        # -------------------------------------------------
        # Semantic search
        # -------------------------------------------------

        embeddings = (
            self._get_embedding_provider()
            .embed([query])
        )

        if len(embeddings) != 1:
            raise ValueError(
                "Query embedding provider must "
                "return exactly one embedding."
            )

        vector_matches = (
            self.vector_repository.search(
                embeddings[0],
                top_k,
                document_ids=[
                    str(document_id)
                    for document_id in eligible_ids
                ],
            )
        )

        scores: dict[int, float] = {}
        snippets: dict[
            int,
            tuple[float, str],
        ] = {}

        for match in vector_matches:

            score = float(match.score)
            document_id = int(
                match.document_id
            )

            if score < MIN_RELEVANCE:
                continue

            scores[document_id] = max(
                scores.get(
                    document_id,
                    float("-inf"),
                ),
                score,
            )

            if score > snippets.get(
                document_id,
                (
                    float("-inf"),
                    "",
                ),
            )[0]:

                snippets[document_id] = (
                    score,
                    match.content,
                )

        # -------------------------------------------------
        # Keyword search
        # -------------------------------------------------

        terms = _keyword_terms(query)

        if terms:

            search_query = SearchQuery(
                " | ".join(terms),
                search_type="raw",
                config="english",
            )

            searchable_chunks = (
                DocumemtsChunk.objects.filter(
                    document_id__in=eligible_ids,
                    document__user_id=user_id,
                    document__is_processed=True,
                    chunks_text__gt="",
                )
                .annotate(
                    search_vector=SearchVector(
                        "chunks_text",
                        config="english",
                    )
                )
                .filter(
                    search_vector=search_query
                )
                .annotate(
                    rank=SearchRank(
                        F("search_vector"),
                        search_query,
                    )
                )
                .order_by(
                    "-rank",
                    "pk",
                )
            )

            for chunk in searchable_chunks:

                document_id = (
                    chunk.document_id
                )

                rank = float(
                    chunk.rank
                )

                if rank <= 0:
                    continue

                keyword_score = (
                    MIN_RELEVANCE
                    + (
                        (1 - MIN_RELEVANCE)
                        * rank
                        / (rank + 0.1)
                    )
                )

                if keyword_score > scores.get(
                    document_id,
                    float("-inf"),
                ):

                    scores[document_id] = (
                        keyword_score
                    )

                    snippets[document_id] = (
                        keyword_score,
                        chunk.chunks_text,
                    )

        return [
            DocumentSearchMatch(
                document_id=document_id,
                relevance_score=score,
                matched_snippet=_snippet(
                    snippets.get(
                        document_id,
                        (0, ""),
                    )[1]
                ),
            )
            for document_id, score in sorted(
                scores.items(),
                key=lambda item: (
                    -item[1],
                    item[0],
                ),
            )[:top_k]
        ]

    def _get_embedding_provider(
        self,
    ) -> EmbeddingProvider:

        if self.embedding_provider is None:

            self.embedding_provider = (
                SentenceTransformerProvider(
                    EmbeddingConfig()
                )
            )

        return self.embedding_provider


def _file_type_extensions() -> tuple[str, ...]:
    return tuple(
        file_type.lower()
        for file_type, _label
        in UploadedDocument.FILE_TYPES_CHOICES
    )


def _extract_requested_file_type(
    query: str,
) -> str | None:

    extensions = (
        _file_type_extensions()
    )

    extension_pattern = "|".join(
        re.escape(extension)
        for extension in extensions
    )

    # Example:
    # "files ending with .pdf"
    # "file name ends with .pdf"
    dotted_match = re.search(
        rf"\.(?P<extension>{extension_pattern})\b",
        query,
        flags=re.IGNORECASE,
    )

    if dotted_match:

        if re.search(
            r"\b(?:end|ends|ending|extension|type)\b",
            query,
            flags=re.IGNORECASE,
        ):
            return dotted_match.group(
                "extension"
            ).lower()

    # Example:
    # "pdf files"
    # "pdf documents"
    type_match = re.search(
        rf"\b(?P<extension>{extension_pattern})\s+"
        r"(?:files?|documents?)\b",
        query,
        flags=re.IGNORECASE,
    )

    if type_match:
        return type_match.group(
            "extension"
        ).lower()

    return None


def _extract_requested_filename(
    query: str,
) -> str | None:

    extensions = "|".join(
        re.escape(file_type)
        for file_type, _label
        in UploadedDocument.FILE_TYPES_CHOICES
    )

    extension_match = re.search(
        rf"\.(?:{extensions})(?=$|[\s,!?])",
        query,
        flags=re.IGNORECASE,
    )

    if extension_match is None:
        return None

    prefix = query[
        :extension_match.start()
    ]

    markers = list(
        re.finditer(
            r"\b(?:named|called|titled|"
            r"find|locate|search(?:\s+for)?)\b",
            prefix,
            flags=re.IGNORECASE,
        )
    )

    # Without a filename marker, this is not
    # treated as an exact filename query.
    if not markers:
        return None

    start = markers[-1].end()

    filename = query[
        start:extension_match.end()
    ].strip().strip(
        "\"'` "
    )

    filename = re.sub(
        r"^(?:(?:me\s+)?"
        r"(?:the\s+)?"
        r"(?:document|file)\s+)+",
        "",
        filename,
        flags=re.IGNORECASE,
    )

    if not re.fullmatch(
        rf"[\w .()_-]+\.(?:{extensions})",
        filename,
        flags=re.IGNORECASE,
    ):
        return None

    return filename


def _keyword_terms(
    query: str,
) -> list[str]:

    return [
        term
        for term in dict.fromkeys(
            re.findall(
                r"\w+",
                query.lower(),
            )
        )
        if (
            len(term) > 1
            and term not in _QUERY_STOP_WORDS
        )
    ]


def _snippet(
    content: str,
    limit: int = 400,
) -> str | None:

    normalized = " ".join(
        content.split()
    )

    if not normalized:
        return None

    if len(normalized) <= limit:
        return normalized

    return (
        f"{normalized[:limit].rstrip()}..."
    )


@lru_cache(maxsize=1)
def get_document_search_service(
) -> DocumentSearchService:

    return DocumentSearchService()
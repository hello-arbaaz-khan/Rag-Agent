import math
import re
from collections import Counter

from RagCore.Chunking.chunk import Chunk
from RagCore.ErrorsHandle.exceptions import RetrievalError


class BM25Result:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        content: str,
        score: float,
        page_number: int | None = None,
        chunk_index: int = 0,
        metadata: dict | None = None,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.content = content
        self.score = score
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.metadata = metadata or {}


class BM25Retriever:
    def __init__(
        self,
        documents: list[Chunk] | None = None,
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        if k1 < 0:
            raise ValueError(
                "k1 must be greater than or equal to zero."
            )

        if not 0 <= b <= 1:
            raise ValueError(
                "b must be between 0 and 1."
            )

        self.k1 = k1
        self.b = b

        self.documents: list[Chunk] = []
        self._tokenized_documents: list[list[str]] = []
        self._document_frequencies: Counter[str] = Counter()
        self._average_document_length = 0.0

        if documents is not None:
            self.index(documents)

    def index(
        self,
        documents: list[Chunk],
    ) -> None:
        if not isinstance(documents, list):
            raise RetrievalError(
                "Documents must be a list."
            )

        if any(
            not isinstance(document, Chunk)
            for document in documents
        ):
            raise RetrievalError(
                "Documents must contain Chunk objects."
            )

        self.documents = list(documents)

        self._tokenized_documents = [
            self._tokenize(document.content)
            for document in self.documents
        ]

        self._document_frequencies.clear()

        for tokens in self._tokenized_documents:
            for token in set(tokens):
                self._document_frequencies[token] += 1

        if self._tokenized_documents:
            self._average_document_length = (
                sum(
                    len(tokens)
                    for tokens in self._tokenized_documents
                )
                / len(self._tokenized_documents)
            )
        else:
            self._average_document_length = 0.0

    def search(
        self,
        query: str,
        *,
        top_k: int = 20,
        document_ids: list[str] | None = None,
    ) -> list[BM25Result]:
        if not isinstance(query, str) or not query.strip():
            raise RetrievalError(
                "Query must be a non-empty string."
            )

        if top_k <= 0:
            raise RetrievalError(
                "top_k must be greater than zero."
            )

        if (
            document_ids is not None
            and any(
                not document_id
                for document_id in document_ids
            )
        ):
            raise RetrievalError(
                "document_ids must contain non-empty values."
            )

        if not self.documents:
            return []

        allowed_document_ids = (
            set(document_ids)
            if document_ids is not None
            else None
        )

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        scored: list[BM25Result] = []

        for document, tokens in zip(
            self.documents,
            self._tokenized_documents,
        ):
            if (
                allowed_document_ids is not None
                and document.document_id
                not in allowed_document_ids
            ):
                continue

            score = self._score_document(
                query_tokens,
                tokens,
            )

            if score <= 0:
                continue

            scored.append(
                BM25Result(
                    chunk_id=document.chunk_id,
                    document_id=document.document_id,
                    content=document.content,
                    score=score,
                    page_number=document.page_number,
                    chunk_index=document.chunk_index,
                    metadata=dict(document.metadata),
                )
            )

        scored.sort(
            key=lambda result: (
                -result.score,
                result.chunk_id,
            )
        )

        return scored[:top_k]

    def _score_document(
        self,
        query_tokens: list[str],
        document_tokens: list[str],
    ) -> float:
        document_length = len(document_tokens)

        if document_length == 0:
            return 0.0

        if self._average_document_length == 0:
            return 0.0

        term_frequencies = Counter(
            document_tokens
        )

        document_count = len(
            self.documents
        )

        score = 0.0

        for term in set(query_tokens):
            term_frequency = term_frequencies.get(
                term,
                0,
            )

            if term_frequency == 0:
                continue

            document_frequency = (
                self._document_frequencies.get(
                    term,
                    0,
                )
            )

            if document_frequency == 0:
                continue

            idf = math.log(
                1
                + (
                    document_count
                    - document_frequency
                    + 0.5
                )
                / (
                    document_frequency
                    + 0.5
                )
            )

            normalization = (
                self.k1
                * (
                    1
                    - self.b
                    + self.b
                    * (
                        document_length
                        / self._average_document_length
                    )
                )
            )

            denominator = (
                term_frequency
                + normalization
            )

            score += (
                idf
                * (
                    term_frequency
                    * (self.k1 + 1)
                    / denominator
                )
            )

        return score

    @staticmethod
    def _tokenize(
        text: str,
    ) -> list[str]:
        return re.findall(
            r"\b\w+\b",
            text.lower(),
        )
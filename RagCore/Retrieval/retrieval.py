from math import isfinite
from enum import Enum

from pydantic import BaseModel, Field

from RagCore.ErrorsHandle.exceptions import RetrievalError


class RetrievalMode(str, Enum):
    VECTOR = "vector"
    HYBRID = "hybrid"


class RetrievalConfig(BaseModel):
    top_k: int = Field(default=20, gt=0)
    dimensions: int = Field(default=384, gt=0)
    mode: RetrievalMode = RetrievalMode.VECTOR
    candidate_k: int = Field(default=20, gt=0)
    rrf_k: int = Field(default=60, gt=0)


class RetrievalResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    page_number: int | None = None
    chunk_index: int
    metadata: dict = Field(default_factory=dict)


def validate_query_embedding(
    embedding: list[float],
    dimensions: int,
) -> None:
    if not embedding:
        raise RetrievalError("Query embedding cannot be empty.")

    if len(embedding) != dimensions:
        raise RetrievalError(
            f"Query embedding dimensions must be {dimensions}, "
            f"got {len(embedding)}."
        )

    if not all(
        isinstance(value, (int, float))
        and isfinite(float(value))
        for value in embedding
    ):
        raise RetrievalError(
            "Query embedding must contain only finite numeric values."
        )
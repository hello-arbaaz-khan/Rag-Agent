from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class DocumentSearchRequest(BaseModel):
    query: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Text or topic to search for.",
    )

    uploaded_after: date | None = None

    uploaded_before: date | None = None

    file_type: Literal[
        "pdf",
        "doc",
        "docx",
        "txt",
        "image",
    ] | None = None

    order_by: Literal[
        "uploaded_at",
        "name",
    ] = "uploaded_at"

    order: Literal[
        "asc",
        "desc",
    ] = "desc"

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )


class DocumentSearchResult(BaseModel):
    id: int
    name: str
    file_type: str
    file_size: int
    uploaded_at: datetime
    is_processed: bool
    relevance_score: float | None = None


class DocumentSearchResponse(BaseModel):
    results: list[DocumentSearchResult]
    count: int
    limit: int
    offset: int
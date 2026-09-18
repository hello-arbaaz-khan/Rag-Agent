from typing import Any
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    parent_id: str | None = None

    content: str

    page_number: int | None = None
    chunk_index: int = Field(ge=0)

    metadata: dict[str, Any] = Field(default_factory=dict)


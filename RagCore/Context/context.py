from pydantic import BaseModel, Field


class ContextConfig(BaseModel):
    # Keep enough evidence for comparisons across several documents.
    # This is a maximum, not a guarantee that every document is covered.
    max_chunks: int = Field(default=10, gt=0)
    separator: str = "\n\n---\n\n"


class Context(BaseModel):
    text: str
    sources: list[dict] = Field(default_factory=list)
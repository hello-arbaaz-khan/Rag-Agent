from pydantic import BaseModel, Field


class ContextConfig(BaseModel):
    max_chunks: int = Field(default=5, gt=0)
    separator: str = "\n\n---\n\n"


class Context(BaseModel):
    text: str
    sources: list[dict] = Field(default_factory=list)
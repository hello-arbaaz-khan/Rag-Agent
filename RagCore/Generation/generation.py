from pydantic import BaseModel, Field


class GenerationConfig(BaseModel):
    model: str = "openai/gpt-oss-20b"
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1024, gt=0)
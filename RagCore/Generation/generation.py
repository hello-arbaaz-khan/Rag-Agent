from pydantic import BaseModel, Field


class GenerationConfig(BaseModel):
    model: str = "llama-3.3-70b-versatile"
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1024, gt=0)
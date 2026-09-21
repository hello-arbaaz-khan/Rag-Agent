from pydantic import BaseModel, Field


class RerankingConfig(BaseModel):
    top_k: int = Field(default=5, gt=0)
from pydantic import BaseModel,Field

class EmbeddingConfig(BaseModel):
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = Field(default=32, gt=0)
    normalize_embeddings: bool = False


class EmbeddingResult(BaseModel):
    chunk_id: str
    document_id: str
    embedding: list[float]
    model: str
    dimensions: int = Field(gt=0)
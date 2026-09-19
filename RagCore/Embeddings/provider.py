from typing import Protocol

from sentence_transformers import SentenceTransformer

from .embedding import EmbeddingConfig


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class SentenceTransformerProvider:
    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config
        self.model = SentenceTransformer(config.model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            normalize_embeddings=self.config.normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()
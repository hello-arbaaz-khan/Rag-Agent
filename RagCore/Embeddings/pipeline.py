from .embedding import EmbeddingConfig, EmbeddingResult
from RagCore.Chunking.chunk import Chunk
from .provider import EmbeddingProvider
from RagCore.ErrorsHandle.exceptions import EmbeddingError

class EmbeddingPipeline:
    def __init__(self, provid: EmbeddingProvider, config: EmbeddingConfig) -> None:
        self.provid = provid
        self.config = config
    
    def process(self, chunks: list[Chunk]) -> list[EmbeddingResult]:
        if not chunks:
            return []

        valid_chunks = [chunk for chunk in chunks if chunk.content.strip()]

        if not valid_chunks:
            return []

        texts = [chunk.content for chunk in valid_chunks]
        embeddings = self.provid.embed(texts)

        if len(embeddings) != len(valid_chunks):
            raise EmbeddingError(
                "Embedding provider returned a different number of embeddings "
                "than the number of input chunks."
            )
        
        dimensions = len(embeddings[0])

        if dimensions == 0:
            raise EmbeddingError(
                "Embedding provider returned empty embedding"
            )
        
        if any(len(embedding) != dimensions for embedding in embeddings):
            raise EmbeddingError("Embedding dimensions are inconsistent.")

        return [
            EmbeddingResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                embedding=embedding,
                model=self.config.model,
                dimensions=dimensions,
            )
            for chunk, embedding in zip(valid_chunks, embeddings)
        ]

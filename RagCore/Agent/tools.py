from RagCore.Embeddings.provider import EmbeddingProvider
from RagCore.Query.pipeline import QueryPipeline
from RagCore.Reranking.pipeline import RerankingPipeline
from RagCore.Retrieval.pipeline import RetrievalPipeline
from RagCore.Retrieval.retrieval import RetrievalResult


class DocumentSearchTool:
    def __init__(
        self,
        query_pipeline: QueryPipeline,
        embedding_provider: EmbeddingProvider,
        retrieval_pipeline: RetrievalPipeline,
        reranking_pipeline: RerankingPipeline,
    ) -> None:
        self.query_pipeline = query_pipeline
        self.embedding_provider = embedding_provider
        self.retrieval_pipeline = retrieval_pipeline
        self.reranking_pipeline = reranking_pipeline

    def search(
        self,
        query_text: str,
        *,
        document_ids: list[str] | None = None,
        retrieval_top_k: int = 20,
        reranking_top_k: int = 5,
    ) -> list[RetrievalResult]:
        query = self.query_pipeline.process(query_text)

        embeddings = self.embedding_provider.embed(
            [query.normalize_text()]
        )

        if len(embeddings) != 1:
            raise ValueError(
                "Query embedding provider must return exactly one embedding."
            )

        candidates = self.retrieval_pipeline.retrieve(
            embeddings[0],
            top_k=retrieval_top_k,
            document_ids=document_ids,
        )

        return self.reranking_pipeline.rerank(
            query.normalize_text(),
            candidates,
            top_k=reranking_top_k,
        )
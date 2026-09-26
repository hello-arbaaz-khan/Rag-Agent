from RagCore.Embeddings.provider import EmbeddingProvider
from RagCore.ErrorsHandle.exceptions import EvaluationError
from RagCore.Evaluation.dataset import EvaluationDataset
from RagCore.Evaluation.report import EvaluationReport
from RagCore.Evaluation.retrieval import RetrievalEvaluator
from RagCore.Reranking.pipeline import RerankingPipeline
from RagCore.Retrieval.pipeline import RetrievalPipeline


class EvaluationRunner:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        retrieval_pipeline: RetrievalPipeline,
        retrieval_evaluator: RetrievalEvaluator,
        reranking_pipeline: RerankingPipeline | None = None,
        rerank_top_k: int | None = None,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.retrieval_pipeline = retrieval_pipeline
        self.retrieval_evaluator = retrieval_evaluator
        self.reranking_pipeline = reranking_pipeline
        self.rerank_top_k = rerank_top_k

    def evaluate(
        self,
        dataset: EvaluationDataset,
    ) -> EvaluationReport:
        if not isinstance(dataset, EvaluationDataset):
            raise EvaluationError(
                "dataset must be an EvaluationDataset."
            )

        dataset.validate_non_empty()

        report = EvaluationReport()

        for sample in dataset.samples:
            query = sample.query.strip()

            try:
                embeddings = self.embedding_provider.embed(
                    [query]
                )
            except Exception as exc:
                raise EvaluationError(
                    f"Failed to embed evaluation query: {query}"
                ) from exc

            if len(embeddings) != 1:
                raise EvaluationError(
                    "Embedding provider must return exactly "
                    "one embedding for one evaluation query."
                )

            query_embedding = embeddings[0]

            retrieved_results = self.retrieval_pipeline.retrieve(
                query_embedding,
                query=query,
            )

            results_for_evaluation = retrieved_results

            if self.reranking_pipeline is not None:
                results_for_evaluation = (
                    self.reranking_pipeline.rerank(
                        query,
                        retrieved_results,
                        top_k=self.rerank_top_k,
                    )
                )

            metrics = self.retrieval_evaluator.evaluate(
                sample,
                results_for_evaluation,
            )

            report.add(metrics)

        return report
from functools import lru_cache

from apps.documents.models import DocumemtsChunk

from apps.documents.Retrieval.pgvector_retriever import (
    DjangoPgVectorRepository,
)

from Workflow.chat.processing import (
    ChatQueryWorkflow,
)

from RagCore.Agent.agent import (
    Agent,
    AgentConfig,
)

from RagCore.Agent.executor import (
    AgentExecutor,
)

from RagCore.Agent.planner import (
    AgentPlanner,
)

from RagCore.Agent.tools import (
    DocumentSearchTool,
)

from RagCore.Context.builder import (
    ContextBuilder,
)

from RagCore.Embeddings.embedding import (
    EmbeddingConfig,
)

from RagCore.Embeddings.provider import (
    SentenceTransformerProvider,
)

from RagCore.Generation.generation import (
    GenerationConfig,
)

from RagCore.Generation.pipeline import (
    GenerationPipeline,
)

from RagCore.Generation.provider import (
    GroqProvider,
)

from RagCore.Query.pipeline import (
    QueryPipeline,
)

from RagCore.Reranking.pipeline import (
    RerankingPipeline,
)

from RagCore.Reranking.provider import (
    CrossEncoderRerankerProvider,
)

from RagCore.Reranking.reranking import (
    RerankingConfig,
)

from RagCore.Retrieval.pipeline import (
    RetrievalPipeline,
)

from RagCore.Retrieval.retrieval import (
    RetrievalConfig,
)


@lru_cache(maxsize=1)
def get_chat_workflow() -> ChatQueryWorkflow:

    embedding_config = EmbeddingConfig()

    embedding_provider = (
        SentenceTransformerProvider(
            embedding_config
        )
    )

    repository = (
        DjangoPgVectorRepository(
            DocumemtsChunk
        )
    )

    retrieval_config = RetrievalConfig(
        dimensions=384,
        top_k=20,
    )

    retrieval_pipeline = RetrievalPipeline(
        repository=repository,
        config=retrieval_config,
    )

    # Real production reranker.
    reranker_provider = (
        CrossEncoderRerankerProvider()
    )

    reranking_pipeline = (
        RerankingPipeline(
            provider=reranker_provider,
            config=RerankingConfig(
                top_k=5,
            ),
        )
    )

    query_pipeline = QueryPipeline()

    search_tool = DocumentSearchTool(
        query_pipeline=query_pipeline,
        embedding_provider=embedding_provider,
        retrieval_pipeline=retrieval_pipeline,
        reranking_pipeline=reranking_pipeline,
    )

    agent_config = AgentConfig(
        retrieval_top_k=20,
        reranking_top_k=5,
        max_steps=5,
        max_subqueries=5,
    )

    executor = AgentExecutor(
        search_tool=search_tool,
        max_steps=agent_config.max_steps,
        retrieval_top_k=(
            agent_config.retrieval_top_k
        ),
        reranking_top_k=(
            agent_config.reranking_top_k
        ),
    )

    generation_config = GenerationConfig(
        model="openai/gpt-oss-20b",
    )

    generation_provider = GroqProvider(
        config=generation_config,
    )

    planner = AgentPlanner(
        provider=generation_provider,
        max_subqueries=(
            agent_config.max_subqueries
        ),
    )

    context_builder = ContextBuilder()

    generation_pipeline = (
        GenerationPipeline(
            provider=generation_provider,
            config=generation_config,
        )
    )

    agent = Agent(
        planner=planner,
        executor=executor,
        context_builder=context_builder,
        generation_pipeline=generation_pipeline,
        config=agent_config,
    )

    return ChatQueryWorkflow(
        agent=agent,
    )
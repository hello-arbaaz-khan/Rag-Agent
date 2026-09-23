import json
from unittest.mock import Mock

import pytest

from RagCore.Agent.agent import Agent, AgentConfig
from RagCore.Agent.executor import AgentExecutor
from RagCore.Agent.planner import AgentPlan, AgentPlanner
from RagCore.Agent.state import AgentState
from RagCore.Agent.tools import DocumentSearchTool
from RagCore.ErrorsHandle.exceptions import DocuMindError


def make_result(
    chunk_id: str,
    document_id: str = "document-1",
):
    result = Mock()
    result.chunk_id = chunk_id
    result.document_id = document_id
    result.content = f"Content for {chunk_id}"
    result.score = 0.9
    return result


@pytest.fixture
def planner_provider():
    provider = Mock()
    provider.generate.return_value = json.dumps(
        {
            "queries": [
                "What is authentication?"
            ]
        }
    )
    return provider


@pytest.fixture
def real_planner(planner_provider):
    return AgentPlanner(
        provider=planner_provider,
        max_subqueries=5,
    )


@pytest.fixture
def query_pipeline():
    query = Mock()
    query.normalize_text.return_value = (
        "normalized question"
    )

    pipeline = Mock()
    pipeline.process.return_value = query

    return pipeline


@pytest.fixture
def embedding_provider():
    provider = Mock()
    provider.embed.return_value = [
        [0.1, 0.2, 0.3]
    ]
    return provider


@pytest.fixture
def retrieval_pipeline():
    pipeline = Mock()
    pipeline.retrieve.return_value = [
        make_result("chunk-1"),
        make_result("chunk-2"),
    ]
    return pipeline


@pytest.fixture
def reranking_pipeline():
    pipeline = Mock()
    pipeline.rerank.return_value = [
        make_result("chunk-1"),
    ]
    return pipeline


@pytest.fixture
def real_search_tool(
    query_pipeline,
    embedding_provider,
    retrieval_pipeline,
    reranking_pipeline,
):
    return DocumentSearchTool(
        query_pipeline=query_pipeline,
        embedding_provider=embedding_provider,
        retrieval_pipeline=retrieval_pipeline,
        reranking_pipeline=reranking_pipeline,
    )


@pytest.fixture
def executor_search_tool():
    return Mock()


@pytest.fixture
def real_executor(executor_search_tool):
    return AgentExecutor(
        search_tool=executor_search_tool,
        max_steps=5,
    )


@pytest.fixture
def agent_planner():
    planner = Mock()
    planner.plan.return_value = AgentPlan(
        queries=[
            "What is RAG?"
        ]
    )
    return planner


@pytest.fixture
def agent_executor():
    executor = Mock()
    executor.execute.return_value = [
        make_result("chunk-1")
    ]
    return executor


@pytest.fixture
def context_builder():
    builder = Mock()
    builder.build.return_value = "Relevant context"
    return builder


@pytest.fixture
def generation_pipeline():
    generator = Mock()
    generator.generate.return_value = "Final answer"
    return generator


@pytest.fixture
def agent(
    agent_planner,
    agent_executor,
    context_builder,
    generation_pipeline,
):
    return Agent(
        planner=agent_planner,
        executor=agent_executor,
        context_builder=context_builder,
        generation_pipeline=generation_pipeline,
        config=AgentConfig(
            retrieval_top_k=20,
            reranking_top_k=5,
            max_steps=5,
            max_subqueries=5,
        ),
    )


def test_agent_state_defaults():
    state = AgentState(
        question="What is RAG?"
    )

    assert state.question == "What is RAG?"
    assert state.document_ids is None
    assert state.conversation_context == ""
    assert state.subqueries == []
    assert state.completed_queries == []
    assert state.retrieval_attempts == 0
    assert state.candidates_count == 0
    assert state.final_answer is None


def test_planner_creates_single_query(
    real_planner,
    planner_provider,
):
    plan = real_planner.plan(
        "What is authentication?"
    )

    assert plan.queries == [
        "What is authentication?"
    ]

    assert plan.is_multi_step is False

    planner_provider.generate.assert_called_once()


def test_planner_creates_multiple_queries(
    real_planner,
    planner_provider,
):
    planner_provider.generate.return_value = json.dumps(
        {
            "queries": [
                "Find authentication information.",
                "Find authorization information.",
                "Find security information.",
            ]
        }
    )

    plan = real_planner.plan(
        "Compare authentication and authorization."
    )

    assert plan.queries == [
        "Find authentication information.",
        "Find authorization information.",
        "Find security information.",
    ]

    assert plan.is_multi_step is True


def test_planner_passes_conversation_context(
    real_planner,
    planner_provider,
):
    real_planner.plan(
        "What about its security?",
        conversation_context=(
            "Previous question: What is OAuth?"
        ),
    )

    planner_provider.generate.assert_called_once()

    _, user_prompt = (
        planner_provider.generate.call_args.args
    )

    assert (
        "Previous question: What is OAuth?"
        in user_prompt
    )


def test_planner_rejects_empty_question(
    real_planner,
):
    with pytest.raises(
        DocuMindError,
        match="non-empty",
    ):
        real_planner.plan("")


def test_planner_rejects_whitespace_question(
    real_planner,
):
    with pytest.raises(
        DocuMindError,
        match="non-empty",
    ):
        real_planner.plan("   ")


def test_planner_wraps_provider_failure(
    real_planner,
    planner_provider,
):
    planner_provider.generate.side_effect = RuntimeError(
        "LLM unavailable"
    )

    with pytest.raises(
        DocuMindError,
        match="LLM unavailable",
    ):
        real_planner.plan(
            "What is RAG?"
        )


def test_planner_rejects_invalid_json(
    real_planner,
    planner_provider,
):
    planner_provider.generate.return_value = (
        "not valid json"
    )

    with pytest.raises(
        DocuMindError,
        match="invalid JSON",
    ):
        real_planner.plan(
            "What is RAG?"
        )


def test_planner_rejects_missing_queries(
    real_planner,
    planner_provider,
):
    planner_provider.generate.return_value = json.dumps(
        {}
    )

    with pytest.raises(
        DocuMindError,
        match="queries list",
    ):
        real_planner.plan(
            "What is RAG?"
        )


def test_planner_rejects_empty_queries(
    real_planner,
    planner_provider,
):
    planner_provider.generate.return_value = json.dumps(
        {
            "queries": []
        }
    )

    with pytest.raises(
        DocuMindError,
        match="no usable queries",
    ):
        real_planner.plan(
            "What is RAG?"
        )


def test_planner_limits_maximum_subqueries(
    real_planner,
    planner_provider,
):
    planner_provider.generate.return_value = json.dumps(
        {
            "queries": [
                "query 1",
                "query 2",
                "query 3",
                "query 4",
                "query 5",
                "query 6",
            ]
        }
    )

    plan = real_planner.plan(
        "Complex question"
    )

    assert len(plan.queries) == 5


def test_search_tool_runs_rag_flow(
    real_search_tool,
    query_pipeline,
    embedding_provider,
    retrieval_pipeline,
    reranking_pipeline,
):
    results = real_search_tool.search(
        "What is RAG?"
    )

    assert len(results) == 1

    query_pipeline.process.assert_called_once_with(
        "What is RAG?"
    )

    embedding_provider.embed.assert_called_once_with(
        ["normalized question"]
    )

    retrieval_pipeline.retrieve.assert_called_once_with(
        [0.1, 0.2, 0.3],
        top_k=20,
        document_ids=None,
    )

    reranking_pipeline.rerank.assert_called_once_with(
        "normalized question",
        retrieval_pipeline.retrieve.return_value,
        top_k=5,
    )


def test_search_tool_passes_document_ids(
    real_search_tool,
    retrieval_pipeline,
):
    document_ids = [
        "document-1",
        "document-2",
    ]

    real_search_tool.search(
        "authentication",
        document_ids=document_ids,
    )

    retrieval_pipeline.retrieve.assert_called_once_with(
        [0.1, 0.2, 0.3],
        top_k=20,
        document_ids=document_ids,
    )


def test_search_tool_rejects_multiple_embeddings(
    real_search_tool,
    embedding_provider,
):
    embedding_provider.embed.return_value = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    with pytest.raises(
        ValueError,
        match="exactly one embedding",
    ):
        real_search_tool.search(
            "What is RAG?"
        )


def test_search_tool_propagates_query_failure(
    real_search_tool,
    query_pipeline,
):
    query_pipeline.process.side_effect = RuntimeError(
        "query failed"
    )

    with pytest.raises(
        RuntimeError,
        match="query failed",
    ):
        real_search_tool.search(
            "What is RAG?"
        )


def test_search_tool_propagates_retrieval_failure(
    real_search_tool,
    retrieval_pipeline,
):
    retrieval_pipeline.retrieve.side_effect = RuntimeError(
        "database unavailable"
    )

    with pytest.raises(
        RuntimeError,
        match="database unavailable",
    ):
        real_search_tool.search(
            "What is RAG?"
        )


def test_executor_executes_single_query(
    real_executor,
    executor_search_tool,
):
    executor_search_tool.search.return_value = [
        make_result("chunk-1")
    ]

    state = AgentState(
        question="What is RAG?"
    )

    results = real_executor.execute(
        ["What is RAG?"],
        state,
    )

    assert len(results) == 1

    executor_search_tool.search.assert_called_once_with(
        "What is RAG?",
        document_ids=None,
    )

    assert state.retrieval_attempts == 1

    assert state.completed_queries == [
        "What is RAG?"
    ]


def test_executor_executes_multiple_queries(
    real_executor,
    executor_search_tool,
):
    executor_search_tool.search.side_effect = [
        [make_result("chunk-1")],
        [make_result("chunk-2")],
        [make_result("chunk-3")],
    ]

    state = AgentState(
        question=(
            "Compare authentication and authorization."
        )
    )

    results = real_executor.execute(
        [
            "Find authentication.",
            "Find authorization.",
            "Find security.",
        ],
        state,
    )

    assert len(results) == 3

    assert executor_search_tool.search.call_count == 3

    assert state.retrieval_attempts == 3

    assert state.completed_queries == [
        "Find authentication.",
        "Find authorization.",
        "Find security.",
    ]


def test_executor_passes_document_ids(
    real_executor,
    executor_search_tool,
):
    document_ids = [
        "document-1",
        "document-2",
    ]

    executor_search_tool.search.return_value = [
        make_result("chunk-1")
    ]

    state = AgentState(
        question="What is common?",
        document_ids=document_ids,
    )

    real_executor.execute(
        ["Find common information."],
        state,
    )

    executor_search_tool.search.assert_called_once_with(
        "Find common information.",
        document_ids=document_ids,
    )


def test_executor_removes_duplicate_chunks(
    real_executor,
    executor_search_tool,
):
    duplicate_1 = make_result("chunk-1")
    duplicate_2 = make_result("chunk-1")

    executor_search_tool.search.side_effect = [
        [duplicate_1],
        [duplicate_2],
    ]

    state = AgentState(
        question="What is common?"
    )

    results = real_executor.execute(
        [
            "query 1",
            "query 2",
        ],
        state,
    )

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"


def test_executor_rejects_empty_queries(
    real_executor,
):
    state = AgentState(
        question="What is RAG?"
    )

    with pytest.raises(
        DocuMindError,
        match="no queries",
    ):
        real_executor.execute(
            [],
            state,
        )


def test_executor_enforces_max_steps(
    executor_search_tool,
):
    executor = AgentExecutor(
        search_tool=executor_search_tool,
        max_steps=2,
    )

    state = AgentState(
        question="Complex question"
    )

    with pytest.raises(
        DocuMindError,
        match="maximum execution steps",
    ):
        executor.execute(
            [
                "query 1",
                "query 2",
                "query 3",
            ],
            state,
        )


def test_executor_updates_candidate_count(
    real_executor,
    executor_search_tool,
):
    executor_search_tool.search.side_effect = [
        [
            make_result("chunk-1"),
            make_result("chunk-2"),
        ],
        [
            make_result("chunk-3"),
        ],
    ]

    state = AgentState(
        question="What is common?"
    )

    results = real_executor.execute(
        [
            "query 1",
            "query 2",
        ],
        state,
    )

    assert len(results) == 3
    assert state.candidates_count == 3


def test_agent_runs_complete_flow(
    agent,
    agent_planner,
    agent_executor,
    context_builder,
    generation_pipeline,
):
    answer = agent.run(
        "What is RAG?"
    )

    assert answer == "Final answer"

    agent_planner.plan.assert_called_once_with(
        "What is RAG?",
        conversation_context="",
    )

    agent_executor.execute.assert_called_once()

    context_builder.build.assert_called_once_with(
        agent_executor.execute.return_value,
    )

    generation_pipeline.generate.assert_called_once()


def test_agent_passes_conversation_context(
    agent,
    agent_planner,
):
    conversation_context = (
        "Previous question: What is OAuth?"
    )

    agent.run(
        "What about its security?",
        conversation_context=conversation_context,
    )

    agent_planner.plan.assert_called_once_with(
        "What about its security?",
        conversation_context=conversation_context,
    )


def test_agent_passes_document_ids(
    agent,
    agent_executor,
):
    document_ids = [
        "document-1",
        "document-2",
    ]

    agent.run(
        "What is common?",
        document_ids=document_ids,
    )

    state = agent_executor.execute.call_args.args[1]

    assert state.document_ids == document_ids


def test_agent_rejects_empty_question(
    agent,
):
    with pytest.raises(
        DocuMindError,
        match="non-empty",
    ):
        agent.run("")


def test_agent_rejects_whitespace_question(
    agent,
):
    with pytest.raises(
        DocuMindError,
        match="non-empty",
    ):
        agent.run("   ")


def test_agent_preserves_final_answer(
    agent,
    generation_pipeline,
):
    generation_pipeline.generate.return_value = (
        "This is the generated answer."
    )

    answer = agent.run(
        "Explain RAG."
    )

    assert answer == (
        "This is the generated answer."
    )


def test_agent_generation_failure(
    agent,
    generation_pipeline,
):
    generation_pipeline.generate.side_effect = (
        RuntimeError(
            "generation failed"
        )
    )

    with pytest.raises(
        DocuMindError,
        match="generation failed",
    ):
        agent.run(
            "Explain RAG."
        )


def test_agent_planner_failure(
    agent,
    agent_planner,
):
    agent_planner.plan.side_effect = DocuMindError(
        "planning failed"
    )

    with pytest.raises(
        DocuMindError,
        match="planning failed",
    ):
        agent.run(
            "Explain RAG."
        )


def test_agent_executor_failure(
    agent,
    agent_executor,
):
    agent_executor.execute.side_effect = DocuMindError(
        "execution failed"
    )

    with pytest.raises(
        DocuMindError,
        match="execution failed",
    ):
        agent.run(
            "Explain RAG."
        )


def test_agent_context_failure(
    agent,
    context_builder,
):
    context_builder.build.side_effect = RuntimeError(
        "context failed"
    )

    with pytest.raises(
        DocuMindError,
        match="context failed",
    ):
        agent.run(
            "Explain RAG."
        )


def test_agent_uses_planner_queries(
    agent,
    agent_planner,
    agent_executor,
):
    agent_planner.plan.return_value = AgentPlan(
        queries=[
            "authentication",
            "authorization",
        ]
    )

    agent.run(
        "Compare authentication and authorization."
    )

    agent_executor.execute.assert_called_once()

    queries = agent_executor.execute.call_args.args[0]

    assert queries == [
        "authentication",
        "authorization",
    ]


def test_agent_executes_multi_document_plan(
    agent,
    agent_planner,
    agent_executor,
):
    agent_planner.plan.return_value = AgentPlan(
        queries=[
            "Find information from document A.",
            "Find information from document B.",
            "Find information from document C.",
        ]
    )

    agent.run(
        "What information is common across the documents?"
    )

    queries = agent_executor.execute.call_args.args[0]

    assert len(queries) == 3

    assert queries == [
        "Find information from document A.",
        "Find information from document B.",
        "Find information from document C.",
    ]


def test_agent_does_not_call_generation_when_planning_fails(
    agent,
    agent_planner,
    generation_pipeline,
):
    agent_planner.plan.side_effect = DocuMindError(
        "planning failed"
    )

    with pytest.raises(DocuMindError):
        agent.run(
            "Explain RAG."
        )

    generation_pipeline.generate.assert_not_called()


def test_agent_does_not_call_generation_when_execution_fails(
    agent,
    agent_executor,
    generation_pipeline,
):
    agent_executor.execute.side_effect = DocuMindError(
        "execution failed"
    )

    with pytest.raises(DocuMindError):
        agent.run(
            "Explain RAG."
        )

    generation_pipeline.generate.assert_not_called()
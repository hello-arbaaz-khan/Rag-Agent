from unittest.mock import Mock

from RagCore.Agent.agent import Agent
from RagCore.Agent.planner import AgentPlan
from RagCore.Context.context import Context
from RagCore.Query.query import Query


def test_agent_passes_history_to_planner_and_generator():
    planner = Mock()
    planner.plan.return_value = AgentPlan(
        queries=["What are the study's limitations?"]
    )

    executor = Mock()
    executor.execute.return_value = []

    context_builder = Mock()
    context_builder.build.return_value = Context(
        text=(
            "[Source 1]\n"
            "Document: Study.pdf\n"
            "Page: 4\n"
            "Content:\nThe sample size is small."
        ),
        sources=[],
    )

    generation_pipeline = Mock()
    generation_pipeline.generate.return_value = (
        "The study has a small sample size."
    )

    agent = Agent(
        planner=planner,
        executor=executor,
        context_builder=context_builder,
        generation_pipeline=generation_pipeline,
    )

    history = (
        "User: Summarize the study.\n"
        "Assistant: The study evaluates a new method."
    )

    answer = agent.run(
        "What are its limitations?",
        document_ids=["17", "18"],
        conversation_context=history,
    )

    assert answer == "The study has a small sample size."

    planner.plan.assert_called_once_with(
        "What are its limitations?",
        conversation_context=history,
    )

    state = executor.execute.call_args.args[1]
    assert state.document_ids == ["17", "18"]
    assert state.conversation_context == history

    args = generation_pipeline.generate.call_args
    assert args.args[0].normalize_text() == (
        Query(text="What are its limitations?").normalize_text()
    )
    assert args.kwargs["conversation_context"] == history
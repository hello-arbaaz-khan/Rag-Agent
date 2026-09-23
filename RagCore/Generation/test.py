import pytest
from pydantic import ValidationError

from RagCore.Context.context import Context
from RagCore.ErrorsHandle.exceptions import GenerationError
from RagCore.Generation.generation import GenerationConfig
from RagCore.Generation.pipeline import GenerationPipeline
from RagCore.Query.query import Query


class FakeGenerationProvider:
    def __init__(self, response="Generated answer"):
        self.response = response
        self.calls = []

    def generate(self, system_prompt, user_prompt):
        self.calls.append(
            (
                system_prompt,
                user_prompt,
            )
        )
        return self.response


def make_query(text="What is RAG?"):
    return Query(text=text)


def make_context(
    text="RAG combines retrieval with generation.",
    sources=None,
):
    return Context(
        text=text,
        sources=[] if sources is None else sources,
    )


def test_generation_config_defaults():
    config = GenerationConfig()

    assert config.model == "llama-3.3-70b-versatile"
    assert config.temperature == 0.2
    assert config.max_tokens == 1024


def test_generation_config_rejects_invalid_temperature():
    with pytest.raises(ValidationError):
        GenerationConfig(temperature=-1)


def test_generation_config_rejects_invalid_max_tokens():
    with pytest.raises(ValidationError):
        GenerationConfig(max_tokens=0)


def test_generation_returns_provider_response():
    provider = FakeGenerationProvider(
        response="RAG retrieves relevant information before generation."
    )

    pipeline = GenerationPipeline(provider)

    answer = pipeline.generate(
        make_query(),
        make_context(),
    )

    assert answer == (
        "RAG retrieves relevant information before generation."
    )


def test_generation_builds_prompt_from_query_and_context():
    provider = FakeGenerationProvider()

    pipeline = GenerationPipeline(provider)

    pipeline.generate(
        Query(text="  What is RAG?  "),
        Context(
            text="RAG retrieves relevant documents.",
            sources=[],
        ),
    )

    system_prompt, user_prompt = provider.calls[0]

    assert "retrieves relevant documents" in user_prompt
    assert "What is RAG?" in user_prompt
    assert "  What is RAG?  " not in user_prompt
    assert "provided context" in system_prompt


def test_generation_handles_empty_context():
    provider = FakeGenerationProvider(
        response="The available context does not contain enough information."
    )

    pipeline = GenerationPipeline(provider)

    answer = pipeline.generate(
        make_query(),
        Context(
            text="",
            sources=[],
        ),
    )

    assert answer == (
        "The available context does not contain enough information."
    )

    _, user_prompt = provider.calls[0]

    assert "Context:" in user_prompt
    assert "Question:" in user_prompt


def test_generation_preserves_context_sources_for_prompt_stage():
    sources = [
        {
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "page_number": 2,
            "chunk_index": 0,
            "metadata": {},
        }
    ]

    context = Context(
        text="Important document information.",
        sources=sources,
    )

    provider = FakeGenerationProvider()

    pipeline = GenerationPipeline(provider)

    pipeline.generate(
        make_query(),
        context,
    )

    assert context.sources == sources


def test_generation_wraps_provider_error():
    class BrokenProvider:
        def generate(self, system_prompt, user_prompt):
            raise RuntimeError("LLM unavailable")

    pipeline = GenerationPipeline(BrokenProvider())

    with pytest.raises(
        GenerationError,
        match="LLM unavailable",
    ):
        pipeline.generate(
            make_query(),
            make_context(),
        )


def test_generation_rejects_invalid_query():
    provider = FakeGenerationProvider()

    pipeline = GenerationPipeline(provider)

    with pytest.raises(GenerationError):
        pipeline.generate(
            "invalid query",
            make_context(),
        )


def test_generation_rejects_invalid_context():
    provider = FakeGenerationProvider()

    pipeline = GenerationPipeline(provider)

    with pytest.raises(GenerationError):
        pipeline.generate(
            make_query(),
            "invalid context",
        )


def test_generation_rejects_empty_provider_response():
    provider = FakeGenerationProvider(
        response="   "
    )

    pipeline = GenerationPipeline(provider)

    with pytest.raises(
        GenerationError,
        match="empty response",
    ):
        pipeline.generate(
            make_query(),
            make_context(),
        )
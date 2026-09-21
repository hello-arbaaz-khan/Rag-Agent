import pytest

from RagCore.ErrorsHandle.exceptions import QueryError
from RagCore.Query.pipeline import QueryPipeline


@pytest.fixture
def query_pipeline():
    return QueryPipeline()


def test_valid_query(query_pipeline):
    result = query_pipeline.process("What is retrieval augmented generation?")

    assert result.text == "What is retrieval augmented generation?"
    assert result.normalize_text() == "What is retrieval augmented generation?"


def test_leading_and_trailing_whitespace(query_pipeline):
    result = query_pipeline.process("   What is RAG?   ")

    assert result.text == "What is RAG?"
    assert result.normalize_text() == "What is RAG?"


@pytest.mark.parametrize(
    "query",
    [
        "",
        " ",
        "   ",
        "\t",
        "\n",
        "\n\t ",
    ],
)
def test_empty_or_whitespace_query(query_pipeline, query):
    with pytest.raises(QueryError, match="Query cannot be empty."):
        query_pipeline.process(query)


@pytest.mark.parametrize(
    "query",
    [
        None,
        123,
        12.5,
        [],
        {},
        True,
    ],
)
def test_invalid_query_type(query_pipeline, query):
    with pytest.raises(QueryError, match="Query must be a string."):
        query_pipeline.process(query)


def test_unicode_query(query_pipeline):
    query = "پاکستان میں RAG کیسے کام کرتا ہے؟"

    result = query_pipeline.process(query)

    assert result.text == query
    assert result.normalize_text() == query


def test_multiline_query(query_pipeline):
    query = "What is RAG?\nHow does retrieval work?"

    result = query_pipeline.process(query)

    assert result.text == query
    assert result.normalize_text() == query


def test_long_query(query_pipeline):
    query = "What is retrieval? " * 1000

    result = query_pipeline.process(query)

    assert result.text == query.strip()
    assert result.normalize_text() == query.strip()


def test_normal_query_is_preserved(query_pipeline):
    query = "How does vector search find relevant chunks?"

    result = query_pipeline.process(query)

    assert result.text == query


def test_query_object_contains_only_normalized_input(query_pipeline):
    query = "   Explain embeddings in RAG.   "

    result = query_pipeline.process(query)

    assert result.text == "Explain embeddings in RAG."

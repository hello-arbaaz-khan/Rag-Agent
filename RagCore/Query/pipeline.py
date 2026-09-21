from RagCore.ErrorsHandle.exceptions import QueryError

from .query import Query


class QueryPipeline:
    def process(self, text: str) -> Query:
        if not isinstance(text, str):
            raise QueryError("Query must be a string.")

        normalized_text = text.strip()

        if not normalized_text:
            raise QueryError("Query cannot be empty.")

        return Query(text=normalized_text)
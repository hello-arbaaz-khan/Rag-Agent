from typing import Protocol


class RerankerProvider(Protocol):
    def score(self,query: str,contents: list[str]) -> list[float]:
        ...


class PassthroughRerankerProvider:
    def score(self, query: str, contents: list[str]) -> list[float]:
        return [1.0] * len(contents)
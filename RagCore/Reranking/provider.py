from typing import Protocol


class RerankerProvider(Protocol):
    def score(self,query: str,contents: list[str]) -> list[float]:
        ...
from dataclasses import dataclass

from .parser import StructuralUnit


@dataclass(frozen=True)
class SplitterConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 100


class ChunkSplitter:
    def __init__(self, config: SplitterConfig | None = None) -> None:
        self.config = config or SplitterConfig()
        self._validate_config()

    def _validate_config(self) -> None:
        if self.config.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if self.config.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if self.config.chunk_overlap >= self.config.chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

    def split(self, units: list[StructuralUnit]) -> list[str]:
        chunks: list[str] = []
        current: list[str] = []
        current_size = 0

        for unit in units:
            content = unit.content.strip()

            if not content:
                continue

            if len(content) > self.config.chunk_size:
                if current:
                    chunks.append("\n\n".join(current))
                    current = []
                    current_size = 0

                chunks.extend(self._split_large_unit(content))
                continue

            separator_size = 2 if current else 0
            required_size = (
                current_size
                + separator_size
                + len(content)
            )

            if current and required_size > self.config.chunk_size:
                chunks.append("\n\n".join(current))
                overlap = self._get_overlap(current)
                current = [overlap] if overlap else []
                current_size = len(overlap) if overlap else 0

            current.append(content)
            current_size += len(content)

            if len(current) > 1:
                current_size += 2

        if current:
            chunks.append("\n\n".join(current))

        return chunks

    def _split_large_unit(self, content: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        step = self.config.chunk_size - self.config.chunk_overlap

        while start < len(content):
            end = min(
                start + self.config.chunk_size,
                len(content),
            )
            piece = content[start:end].strip()

            if piece:
                chunks.append(piece)

            if end >= len(content):
                break

            start += step

        return chunks

    def _get_overlap(self, units: list[str]) -> str:
        if self.config.chunk_overlap == 0:
            return ""

        text = "\n\n".join(units)
        return text[-self.config.chunk_overlap:]
from dataclasses import dataclass, field


@dataclass
class ExtractedPage:

    page_number: int
    text: str


@dataclass
class ChunkData:

    chunk_text: str
    chunk_index: int
    page_number: int
    chunk_size: int
    embedding: list[float] | None = field(default=None)


@dataclass
class IngestionResult:

    chunks: list[ChunkData]

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)
from RagCore.Ingestion.document import InternalDocument

from .chunk import Chunk
from .parser import MarkdownParser
from .splitter import ChunkSplitter


class ChunkingPipeline:
    def __init__(
        self,
        parser: MarkdownParser | None = None,
        splitter: ChunkSplitter | None = None,
    ) -> None:
        self.parser = parser or MarkdownParser()
        self.splitter = splitter or ChunkSplitter()

    def process(self, document: InternalDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_index = 0

        for page in document.pages:
            units = self.parser.parse(page.content)

            if not units:
                continue

            page_chunks = self.splitter.split(units)

            for content in page_chunks:
                chunk = Chunk(
                    chunk_id=f"{document.document_id}:{chunk_index}",
                    document_id=document.document_id,
                    content=content,
                    page_number=page.page_number,
                    chunk_index=chunk_index,
                    metadata=self._build_metadata(units),
                )

                chunks.append(chunk)
                chunk_index += 1

        return chunks

    def _build_metadata(
        self,
        units: list,
    ) -> dict[str, object]:
        metadata: dict[str, object] = {}

        if units:
            metadata["structure_types"] = [
                unit.unit_type for unit in units
            ]

            headings = [
                unit.content
                for unit in units
                if unit.unit_type == "heading"
            ]

            if headings:
                metadata["headings"] = headings

        return metadata
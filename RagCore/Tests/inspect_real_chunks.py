from pathlib import Path

from RagCore.Ingestion.pipeline import IngestionPipeline
from RagCore.Chunking.pipeline import ChunkingPipeline


PDF_DIR = Path(__file__).parent / "Fixtures" / "Pdf_samples"
DOCX_DIR = Path(__file__).parent / "Fixtures" / "Docx_samples"


def inspect_file(file_path: Path):
    ingestion = IngestionPipeline()
    chunking = ChunkingPipeline()

    document = ingestion.run(
        file_path=str(file_path),
        document_id=file_path.stem,
    )

    chunks = chunking.process(document)

    print(f"\n{'=' * 80}")
    print(f"FILE: {file_path.name}")
    print(f"DOCUMENT ID: {document.document_id}")
    print(f"TOTAL CHUNKS: {len(chunks)}")
    print(f"{'=' * 80}")

    for chunk in chunks:
        print(f"\nCHUNK ID: {chunk.chunk_id}")
        print(f"PAGE: {chunk.page_number}")
        print("-" * 80)
        print(chunk.content)
        print("-" * 80)


for directory, extension in [
    (PDF_DIR, ".pdf"),
    (DOCX_DIR, ".docx"),
]:
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == extension:
            inspect_file(file_path)
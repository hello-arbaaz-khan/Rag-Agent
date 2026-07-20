import re

from django.db.models import Count
from rag.models import DriveDocument
from rag.utils.vector_store import search_all_documents


SYNC_STATUS_ORDER = {"indexed": 0, "processing": 1, "pending": 2, "failed": 3}


def _tokenize(text):
    """Split text into lowercase words, ignoring short/noise tokens."""
    return [t for t in re.split(r"\W+", text.lower()) if len(t) > 1]


def score_filename_match(file_name, query):
    """
    Score how well a file's name matches the search query.
    Returns a float between 0 and 1 (1 = perfect/strong match).
    """
    if not file_name or not query:
        return 0.0

    name_lower = file_name.lower()
    query_lower = query.lower().strip()

    if query_lower in name_lower:
        return 1.0

    query_words = _tokenize(query_lower)
    if not query_words:
        return 0.0

    name_words = set(_tokenize(name_lower))
    matched = sum(1 for word in query_words if word in name_words)

    return round(matched / len(query_words), 4)


def _serialize_drive_doc(doc):
    total_chunks = getattr(doc, "total_chunks", None)
    if total_chunks is None and doc.document:
        total_chunks = doc.document.chunk_count

    return {
        "drive_file_id": doc.drive_file_id,
        "name": doc.name,
        "mime_type": doc.mime_type,
        "drive_modified_at": doc.drive_modified_at,
        "sync_status": doc.sync_status,
        "document_id": doc.document_id,
        "total_chunks": total_chunks,
    }


class SearchService:

    @staticmethod
    def browse():
        """No query — return ALL local Drive files, sorted by sync_status."""
        all_docs = list(
            DriveDocument.objects.select_related("document")
            .annotate(annotated_chunks=Count("document__chunks"))
            .all()
        )
        for doc in all_docs:
            if doc.document_id is None:
                doc.total_chunks = None
            else:
                doc.total_chunks = doc.annotated_chunks

        all_docs.sort(key=lambda d: (SYNC_STATUS_ORDER.get(d.sync_status, 9), d.name.lower()))

        return {
            "results": [_serialize_drive_doc(d) for d in all_docs],
            "total": len(all_docs),
        }

    @staticmethod
    def search(query):
        """Query given — rank ALL local files by combined content + filename relevance."""
        # Layer 1: content matches (only for indexed files) — document_id -> score
        content_matches = search_all_documents(query, top_k=1000)
        content_scores = {m["document_id"]: m["relevance_score"] for m in content_matches}
        content_snippets = {m["document_id"]: m["matched_chunk_text"] for m in content_matches}

        all_docs = list(
            DriveDocument.objects.select_related("document")
            .annotate(annotated_chunks=Count("document__chunks"))
            .all()
        )
        scored = []

        for doc in all_docs:
            if doc.document_id is None:
                doc.total_chunks = None
            else:
                doc.total_chunks = doc.annotated_chunks

            name_score = score_filename_match(doc.name, query)
            content_score = content_scores.get(doc.document_id, 0.0) if doc.document_id else 0.0

            final_score = max(name_score, content_score)
            if final_score <= 0:
                continue  # not relevant at all — leave it out of ranked results

            entry = _serialize_drive_doc(doc)
            entry["relevance_score"] = round(final_score, 4)
            entry["matched_snippet"] = content_snippets.get(doc.document_id)
            scored.append(entry)

        scored.sort(key=lambda item: item["relevance_score"], reverse=True)
        return {
            "results": scored,
            "total": len(scored),
        }
import re
from datetime import datetime

from django.db.models import Count
from django.utils import timezone
from rag.models import DriveDocument
from rag.utils.vector_store import search_all_documents
from rag.utils.query_intent import parse_query_intent


SYNC_STATUS_ORDER = {"indexed": 0, "processing": 1, "pending": 2, "failed": 3}

MIN_RELEVANCE = 0.35


def _parse_iso_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _matches_date_filter(modified_at, date_filter):
    if not date_filter or not date_filter.get("type"):
        return True
    if modified_at is None:
        return False
    doc_date = timezone.localtime(modified_at).date() if timezone.is_aware(modified_at) else modified_at.date()
    filter_type = date_filter["type"]
    start = _parse_iso_date(date_filter.get("date"))
    end = _parse_iso_date(date_filter.get("date_end"))
    if filter_type == "on":
        return start is not None and doc_date == start
    if filter_type == "after":
        return start is not None and doc_date > start
    if filter_type == "before":
        return start is not None and doc_date < start
    if filter_type == "between":
        return start is not None and end is not None and start <= doc_date <= end
    return True


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
        intent = parse_query_intent(query)
        topic = intent["topic"]
        date_filter = intent["date_filter"]

        all_docs = list(
            DriveDocument.objects.select_related("document")
            .annotate(annotated_chunks=Count("document__chunks"))
            .all()
        )

        if date_filter.get("type"):
            all_docs = [d for d in all_docs if _matches_date_filter(d.drive_modified_at, date_filter)]

        scored = []

        if topic:
            content_matches = search_all_documents(topic, top_k=1000)
            content_scores = {m["document_id"]: m["relevance_score"] for m in content_matches}
            content_snippets = {m["document_id"]: m["matched_chunk_text"] for m in content_matches}

            for doc in all_docs:
                if doc.document_id is None:
                    doc.total_chunks = None
                else:
                    doc.total_chunks = doc.annotated_chunks

                name_score = score_filename_match(doc.name, topic)
                content_score = content_scores.get(doc.document_id, 0.0) if doc.document_id else 0.0

                final_score = max(name_score, content_score)
                if final_score < MIN_RELEVANCE:
                    continue

                entry = _serialize_drive_doc(doc)
                entry["relevance_score"] = round(final_score, 4)
                entry["matched_snippet"] = content_snippets.get(doc.document_id)
                scored.append(entry)

            scored.sort(key=lambda item: item["relevance_score"], reverse=True)
        else:
            for doc in all_docs:
                doc.total_chunks = doc.annotated_chunks if doc.document_id else None
                entry = _serialize_drive_doc(doc)
                entry["relevance_score"] = 1.0
                entry["matched_snippet"] = None
                scored.append(entry)
            scored.sort(key=lambda item: item["name"].lower())

        result = {
            "results": scored,
            "total": len(scored),
        }
        if not scored:
            result["message"] = "No matching file found."
        return result
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.documents.models import UploadedDocument
from app.Apis.dependencies import get_current_user
from app.Apis.schemas.search import (
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentSearchResult,
)
from app.Apis.services.chat_workflow import get_chat_workflow


router = APIRouter(
    prefix="/api/v1/search",
    tags=["Document Search"],
)


@router.get(
    "",
    response_model=DocumentSearchResponse,
)
def search_documents(
    filters: Annotated[
        DocumentSearchRequest,
        Query(),
    ],
    user_id: int = Depends(get_current_user),
):
    """
    Search the authenticated user's documents by metadata and content.
    """
    if (
        filters.uploaded_after is not None
        and filters.uploaded_before is not None
        and filters.uploaded_after > filters.uploaded_before
    ):
        raise HTTPException(
            status_code=422,
            detail="uploaded_after must be on or before uploaded_before.",
        )

    query = filters.query.strip() if filters.query is not None else None
    if query == "":
        raise HTTPException(
            status_code=422,
            detail="query must contain non-whitespace text.",
        )

    documents = UploadedDocument.objects.filter(user=user_id)

    if filters.uploaded_after is not None:
        documents = documents.filter(
            created_at__date__gte=filters.uploaded_after
        )

    if filters.uploaded_before is not None:
        documents = documents.filter(
            created_at__date__lte=filters.uploaded_before
        )

    if filters.file_type is not None:
        documents = documents.filter(file_type=filters.file_type)

    if query is None:
        ordering_field = (
            "name"
            if filters.order_by == "name"
            else "created_at"
        )
        ordering = (
            ordering_field
            if filters.order == "asc"
            else f"-{ordering_field}"
        )

        total = documents.count()
        page = documents.order_by(ordering)[
            filters.offset:filters.offset + filters.limit
        ]
        results = [
            DocumentSearchResult(
                id=document.id,
                name=document.name,
                file_type=document.file_type,
                file_size=document.file_size,
                uploaded_at=document.created_at,
                is_processed=document.is_processed,
            )
            for document in page
        ]

        return DocumentSearchResponse(
            results=results,
            count=total,
            limit=filters.limit,
            offset=filters.offset,
        )

    eligible_documents = list(
        documents.filter(is_processed=True)
    )

    if not eligible_documents:
        return DocumentSearchResponse(
            results=[],
            count=0,
            limit=filters.limit,
            offset=filters.offset,
        )

    try:
        search_tool = (
            get_chat_workflow()
            .agent.executor.search_tool
        )
        candidate_limit = min(
            1000,
            max(100, filters.offset + filters.limit),
        )
        matches = search_tool.search(
            query,
            document_ids=[
                str(document.id)
                for document in eligible_documents
            ],
            retrieval_top_k=candidate_limit,
            reranking_top_k=candidate_limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Document search failed.",
        ) from exc

    best_scores = {}
    for match in matches:
        document_id = int(match.document_id)
        best_scores[document_id] = max(
            best_scores.get(document_id, float("-inf")),
            match.score,
        )

    documents_by_id = {
        document.id: document
        for document in eligible_documents
    }
    ranked_documents = [
        (documents_by_id[document_id], score)
        for document_id, score in best_scores.items()
        if document_id in documents_by_id
    ]

    ordering_field = (
        "name"
        if filters.order_by == "name"
        else "created_at"
    )
    ranked_documents.sort(
        key=lambda item: getattr(item[0], ordering_field),
        reverse=filters.order == "desc",
    )

    total = len(ranked_documents)
    page = ranked_documents[
        filters.offset:filters.offset + filters.limit
    ]
    results = [
        DocumentSearchResult(
            id=document.id,
            name=document.name,
            file_type=document.file_type,
            file_size=document.file_size,
            uploaded_at=document.created_at,
            is_processed=document.is_processed,
            relevance_score=score,
        )
        for document, score in page
    ]

    return DocumentSearchResponse(
        results=results,
        count=total,
        limit=filters.limit,
        offset=filters.offset,
    )
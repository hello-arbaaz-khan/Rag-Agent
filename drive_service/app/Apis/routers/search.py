from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.documents.models import UploadedDocument
from apps.documents.services.search import (
    DocumentSearchService,
    get_document_search_service,
)
from app.Apis.dependencies import get_current_user
from app.Apis.schemas.search import (
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentSearchResult,
)


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
    search_service: DocumentSearchService = Depends(
        get_document_search_service
    ),
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

    documents = UploadedDocument.objects.filter(user_id=user_id)

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

    try:
        candidate_limit = min(
            1000,
            max(100, filters.offset + filters.limit),
        )
        matches = search_service.search(
            query,
            user_id=user_id,
            documents=documents,
            top_k=candidate_limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Document search failed.",
        ) from exc

    documents_by_id = documents.in_bulk(
        [match.document_id for match in matches]
    )
    ranked_documents = [
        (match, documents_by_id[match.document_id])
        for match in matches
        if match.document_id in documents_by_id
    ]

    if filters.order_by == "name":
        ranked_documents.sort(
            key=lambda item: item[1].name.lower(),
            reverse=filters.order == "desc",
        )
    elif filters.order_by == "uploaded_at":
        ranked_documents.sort(
            key=lambda item: item[1].created_at,
            reverse=filters.order == "desc",
        )
    else:
        ranked_documents.sort(
            key=lambda item: item[0].relevance_score,
            reverse=True,
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
            relevance_score=match.relevance_score,
            matched_snippet=match.matched_snippet,
        )
        for match, document in page
    ]

    return DocumentSearchResponse(
        results=results,
        count=total,
        limit=filters.limit,
        offset=filters.offset,
    )

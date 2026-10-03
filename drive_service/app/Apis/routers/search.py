from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.Apis.dependencies import get_current_user
from app.Apis.schemas.search import (
    DocumentSearchRequest,
    DocumentSearchResponse,
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
):
    """
    Advanced document discovery.

    Searches the authenticated user's documents using
    content/metadata criteria and document metadata filters.
    """

    # IMPORTANT:
    # Call the existing document-search/application functionality here.
    #
    # Do not put database/RAG search implementation in this router.
    #
    # result = document_search_workflow.search(
    #     user_id=user_id,
    #     query=filters.query,
    #     uploaded_after=filters.uploaded_after,
    #     uploaded_before=filters.uploaded_before,
    #     file_type=filters.file_type,
    #     order_by=filters.order_by,
    #     order=filters.order,
    #     limit=filters.limit,
    #     offset=filters.offset,
    # )

    raise NotImplementedError(
        "Connect this router to the existing document-search implementation."
    )
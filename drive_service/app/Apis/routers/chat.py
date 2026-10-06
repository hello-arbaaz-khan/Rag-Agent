from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.Apis.dependencies import (
    get_current_user,
)

from apps.chat.models import ChatHistory
from apps.documents.models import UploadedDocument

from app.Apis.schemas.chat import (
    ChatHistoryItem,
    ChatRequest,
    ChatResponse,
)

from app.Apis.services.chat_workflow import (
    get_chat_workflow,
)

from RagCore.ErrorsHandle.exceptions import (
    IntegrationError,
)


router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    user=Depends(get_current_user),
    workflow=Depends(get_chat_workflow),
):
    try:
        result = workflow.run(
            user=user,
            question=request.question,
            document_id=request.document_id,
        )

    except IntegrationError as exc:
        message = str(exc)

        if (
            "not found" in message.lower()
            or "access" in message.lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        if "not ready" in message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request.",
        ) from exc

    return ChatResponse(
        question=result.question,
        answer=result.answer,
        document_id=result.document_id,
        document_name=result.document_name,
        chat_history_id=result.chat_history_id,
    )


def _require_owned_document(document_id: int, user_id: int) -> None:
    owned = UploadedDocument.objects.filter(
        id=document_id,
        user_id=user_id,
    ).exists()

    if not owned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )


@router.get(
    "/history/{document_id}",
    response_model=list[ChatHistoryItem],
)
def get_chat_history(
    document_id: int,
    user=Depends(get_current_user),
):
    _require_owned_document(document_id, user)

    return list(
        ChatHistory.objects
        .filter(document_id=document_id)
        .order_by("created_at")
    )


@router.delete(
    "/history/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def clear_chat_history(
    document_id: int,
    user=Depends(get_current_user),
):
    _require_owned_document(document_id, user)

    ChatHistory.objects.filter(document_id=document_id).delete()

    return None
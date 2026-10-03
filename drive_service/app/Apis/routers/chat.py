from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.Apis.dependencies import (
    get_current_user,
)

from app.Apis.schemas.chat import (
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
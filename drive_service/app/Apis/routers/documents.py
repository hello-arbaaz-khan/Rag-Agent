from __future__ import annotations

import hashlib
from pathlib import Path

from django.core.files.base import ContentFile

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    status,
)

from apps.documents.models import UploadedDocument
from apps.documents.tasks import process_document_task
from RagCore.Ingestion.document import ALL_ALLOWED_EXTENSIONS

from app.Apis.dependencies import (
    get_current_user,
)

from app.Apis.schemas.documents import (
    DocumentResponse,
)


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)


SUPPORTED_FILE_TYPES = {
    extension: extension.lstrip(".")
    for extension in dict.fromkeys(ALL_ALLOWED_EXTENSIONS)
}
MAX_UPLOAD_SIZE = 50 * 1024 * 1024


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def upload_document(
    file: UploadFile,
    user=Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File name is required.",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    file_type = SUPPORTED_FILE_TYPES.get(
        extension
    )

    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported document type.",
        )

    content = file.file.read(MAX_UPLOAD_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    file_size = len(content)

    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must not exceed 50 MB.",
        )

    file_hash = hashlib.sha256(
        content
    ).hexdigest()

    existing = UploadedDocument.objects.filter(
        user_id=user,
        file_hash=file_hash,
    ).first()

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Document already exists.",
                "document_id": existing.id,
            },
        )

    document = UploadedDocument(
        user_id=user,
        name=file.filename,
        file_type=file_type,
        file_size=file_size,
        file_hash=file_hash,
    )

    document.file.save(
        file.filename,
        ContentFile(content),
        save=False,
    )

    document.save()

    try:
        task = process_document_task.delay(document.id)

    except Exception as exc:
        document.processing_error = (
            "Failed to queue document processing."
        )
        document.save(
            update_fields=["processing_error", "updated_at"]
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "Document was uploaded but processing could not be queued.",
                "document_id": document.id,
                "processing_error": document.processing_error,
            },
        ) from exc

    return DocumentResponse.model_validate(document).model_copy(
        update={"processing_task_id": task.id}
    )


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    user=Depends(get_current_user),
):
    return list(
        UploadedDocument.objects
        .filter(user_id=user)
        .order_by("-created_at")
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: int,
    user=Depends(get_current_user),
):
    document = (
        UploadedDocument.objects
        .filter(
            id=document_id,
            user_id=user,
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    document_id: int,
    user=Depends(get_current_user),
):
    document = (
        UploadedDocument.objects
        .filter(
            id=document_id,
            user_id=user,
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    document.delete()

    return None

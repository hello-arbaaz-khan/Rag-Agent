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

from Workflow.documents.document_processing import (
    DocumentProcessingWorkflow,
)

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
    ".pdf": "pdf",
    ".doc": "doc",
    ".docx": "docx",
    ".txt": "txt",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".webp": "image",
    ".tiff": "image",
}


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
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

    content = file.file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    file_size = len(content)

    file_hash = hashlib.sha256(
        content
    ).hexdigest()

    existing = UploadedDocument.objects.filter(
        user=user,
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
        user=user,
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
        workflow = DocumentProcessingWorkflow()

        workflow.process(
            document.id,
        )

        document.refresh_from_db()

    except Exception as exc:
        document.refresh_from_db()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Document processing failed.",
                "document_id": document.id,
                "processing_error": document.processing_error,
            },
        ) from exc

    return document


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    user=Depends(get_current_user),
):
    return list(
        UploadedDocument.objects
        .filter(user=user)
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
            user=user,
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
            user=user,
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
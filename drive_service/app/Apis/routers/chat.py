from __future__ import annotations

import hashlib
from pathlib import Path

from django.core.files.base import ContentFile
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.Apis.dependencies import get_current_user
from app.Apis.schemas.chat import (
    AttachDocumentsRequest,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationDocumentResponse,
    ConversationResponse,
    CreateConversationRequest,
)
from apps.chat.models import ChatMessage, Conversation, ConversationDocument
from apps.documents.models import UploadedDocument
from apps.documents.tasks import process_document_task
from RagCore.ErrorsHandle.exceptions import IntegrationError
from RagCore.Ingestion.document import ALL_ALLOWED_EXTENSIONS

from app.Apis.services.chat_workflow import get_chat_workflow


router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

SUPPORTED_FILE_TYPES = {
    extension: extension.lstrip(".")
    for extension in dict.fromkeys(ALL_ALLOWED_EXTENSIONS)
}
MAX_UPLOAD_SIZE = 50 * 1024 * 1024


def _get_owned_conversation(conversation_id: int, user_id: int) -> Conversation:
    conversation = (
        Conversation.objects
        .filter(id=conversation_id, user_id=user_id)
        .prefetch_related("documents")
        .first()
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return conversation


def _conversation_response(conversation: Conversation) -> ConversationResponse:
    documents = [
        ConversationDocumentResponse.model_validate(document)
        for document in conversation.documents.all().order_by("id")
    ]
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        documents=documents,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _attach_documents(conversation: Conversation, document_ids: list[int], user_id: int) -> None:
    ids = list(dict.fromkeys(document_ids))
    documents = list(
        UploadedDocument.objects.filter(
            id__in=ids,
            user_id=user_id,
        )
    )
    found_ids = {document.id for document in documents}
    missing = [document_id for document_id in ids if document_id not in found_ids]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "One or more documents were not found.", "document_ids": missing},
        )

    ConversationDocument.objects.bulk_create(
        [
            ConversationDocument(
                conversation=conversation,
                document=document,
            )
            for document in documents
        ],
        ignore_conflicts=True,
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    request: CreateConversationRequest,
    user=Depends(get_current_user),
):
    conversation = Conversation.objects.create(
        user_id=user,
        title=request.title.strip() or "New chat",
    )
    if request.document_ids:
        _attach_documents(conversation, request.document_ids, user)
    conversation.refresh_from_db()
    return _conversation_response(conversation)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(user=Depends(get_current_user)):
    conversations = list(
        Conversation.objects
        .filter(user_id=user)
        .prefetch_related("documents")
        .order_by("-updated_at", "-id")
    )
    return [_conversation_response(conversation) for conversation in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    user=Depends(get_current_user),
):
    return _conversation_response(_get_owned_conversation(conversation_id, user))


@router.post("/conversations/{conversation_id}/documents", response_model=ConversationResponse)
def attach_existing_documents(
    conversation_id: int,
    request: AttachDocumentsRequest,
    user=Depends(get_current_user),
):
    conversation = _get_owned_conversation(conversation_id, user)
    _attach_documents(conversation, request.document_ids, user)
    conversation.refresh_from_db()
    conversation = _get_owned_conversation(conversation_id, user)
    return _conversation_response(conversation)


@router.post("/conversations/{conversation_id}/documents/upload", response_model=ConversationResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_documents_to_conversation(
    conversation_id: int,
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user),
):
    conversation = _get_owned_conversation(conversation_id, user)
    document_ids: list[int] = []

    for file in files:
        if not file.filename:
            raise HTTPException(status_code=422, detail="File name is required.")

        extension = Path(file.filename).suffix.lower()
        file_type = SUPPORTED_FILE_TYPES.get(extension)
        if file_type is None:
            raise HTTPException(status_code=422, detail=f"Unsupported document type: {file.filename}")

        content = file.file.read(MAX_UPLOAD_SIZE + 1)
        if not content:
            raise HTTPException(status_code=422, detail=f"Uploaded file is empty: {file.filename}")
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail=f"File size must not exceed 50 MB: {file.filename}")

        file_hash = hashlib.sha256(content).hexdigest()
        document = UploadedDocument.objects.filter(
            user_id=user,
            file_hash=file_hash,
        ).first()

        if document is None:
            document = UploadedDocument(
                user_id=user,
                name=file.filename,
                file_type=file_type,
                source=UploadedDocument.Source.UPLOAD,
                file_size=len(content),
                file_hash=file_hash,
            )
            document.file.save(
                file.filename,
                ContentFile(content),
                save=False,
            )
            document.save()

            try:
                process_document_task.delay(document.id)
            except Exception as exc:
                document.processing_error = "Failed to queue document processing."
                document.save(update_fields=["processing_error", "updated_at"])
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={"message": "Document was uploaded but processing could not be queued.", "document_id": document.id},
                ) from exc

        document_ids.append(document.id)

    _attach_documents(conversation, document_ids, user)
    conversation = _get_owned_conversation(conversation_id, user)
    return _conversation_response(conversation)


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
def send_message(
    conversation_id: int,
    request: ChatRequest,
    user=Depends(get_current_user),
    workflow=Depends(get_chat_workflow),
):
    try:
        result = workflow.run(
            user=user,
            question=request.question,
            conversation_id=conversation_id,
        )
    except IntegrationError as exc:
        message = str(exc)
        if "not found" in message.lower() or "access" in message.lower():
            raise HTTPException(status_code=404, detail=message) from exc
        if "not ready" in message.lower() or "no documents" in message.lower():
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=422, detail=message) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to process chat request.") from exc

    return ChatResponse(
        conversation_id=result.conversation_id,
        question=result.question,
        answer=result.answer,
        user_message_id=result.user_message_id,
        assistant_message_id=result.assistant_message_id,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessageResponse])
def get_messages(
    conversation_id: int,
    user=Depends(get_current_user),
):
    conversation = _get_owned_conversation(conversation_id, user)
    return list(
        ChatMessage.objects
        .filter(conversation=conversation)
        .order_by("created_at", "id")
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    user=Depends(get_current_user),
):
    conversation = _get_owned_conversation(conversation_id, user)
    conversation.delete()
    return None
from datetime import datetime

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New chat", min_length=1, max_length=255)
    document_ids: list[int] = Field(default_factory=list)


class AttachDocumentsRequest(BaseModel):
    document_ids: list[int] = Field(..., min_length=1)


class ConversationDocumentResponse(BaseModel):
    id: int
    name: str
    file_type: str
    is_processed: bool
    processing_error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: int
    title: str
    documents: list[ConversationDocumentResponse]
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10_000)


class ChatResponse(BaseModel):
    conversation_id: int
    question: str
    answer: str
    user_message_id: int
    assistant_message_id: int
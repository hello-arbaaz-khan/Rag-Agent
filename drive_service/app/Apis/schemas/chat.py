from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
    )

    document_id: int = Field(
        ...,
        gt=0,
    )


class ChatResponse(BaseModel):
    question: str
    answer: str
    document_id: int
    document_name: str
    chat_history_id: int
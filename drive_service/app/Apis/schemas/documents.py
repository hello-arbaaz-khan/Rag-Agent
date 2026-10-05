from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    name: str
    file_type: str
    source: str
    google_drive_file_id: str | None
    file_size: int
    is_processed: bool
    processing_error: str | None
    processing_task_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DriveFile(BaseModel):
    id: str
    name: str
    mime_type: str
    modified_time: datetime
    trashed: bool = False


class DriveFileListResponse(BaseModel):
    files: list[DriveFile]
    count: int
    next_page_token: str | None = None


class DriveFileDownloadResponse(BaseModel):
    id: str
    name: str
    mime_type: str
    content_base64: str


class DriveSyncQueuedResponse(BaseModel):
    task_id: str
    status: str
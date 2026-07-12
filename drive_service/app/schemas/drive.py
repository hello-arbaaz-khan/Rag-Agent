from datetime import datetime

from pydantic import BaseModel, Field


class DriveFile(BaseModel):
    id: str = Field(..., description="Google Drive file ID")
    name: str
    mime_type: str
    modified_at: datetime | None = None
    size: int | None = None
    web_view_link: str | None = None


class DriveFileListResponse(BaseModel):
    success: bool = True
    data: list[DriveFile]
    count: int


class DriveFileResponse(BaseModel):
    success: bool = True
    data: DriveFile


class DriveDownloadResponse(BaseModel):
    success: bool = True
    data: DriveFile
    content_base64: str

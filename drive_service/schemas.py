from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class DriveFile(BaseModel):
    id: str
    name: str
    mime_type: str
    modified_time: datetime
    trashed: bool = False  # Default False


class DriveFileListResponse(BaseModel):
    files: List[DriveFile]
    count: int
    next_page_token: Optional[str] = None


class DriveFileDownloadResponse(BaseModel):
    id: str
    name: str
    mime_type: str
    content_base64: str
from pydantic import BaseModel


class DriveFileResponse(BaseModel):
    id: str
    name: str
    mime_type: str
    modified_time: str | None = None


class DriveFilesResponse(BaseModel):
    files: list[DriveFileResponse]
    next_page_token: str | None = None


class DriveStatusResponse(BaseModel):
    connected: bool


class DriveSyncResponse(BaseModel):
    synced: int
    failed: int
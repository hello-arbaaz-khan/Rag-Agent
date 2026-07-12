from fastapi import APIRouter, Query

from app.schemas.drive import (
    DriveDownloadResponse,
    DriveFileListResponse,
    DriveFileResponse,
)
from app.services.drive_client import drive_client

router = APIRouter(prefix="/drive", tags=["drive"])


@router.get("/files", response_model=DriveFileListResponse)
def list_drive_files(page_size: int = Query(default=50, ge=1, le=100)):
    files = drive_client.list_files(page_size=page_size)
    return DriveFileListResponse(data=files, count=len(files))


@router.get("/files/{file_id}", response_model=DriveFileResponse)
def get_drive_file(file_id: str):
    file = drive_client.get_file(file_id)
    return DriveFileResponse(data=file)


@router.get("/files/{file_id}/download", response_model=DriveDownloadResponse)
def download_drive_file(file_id: str):
    metadata, content_base64 = drive_client.download_file_base64(file_id)
    return DriveDownloadResponse(data=metadata, content_base64=content_base64)

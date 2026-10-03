from __future__ import annotations

import base64
import socket

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.drive import (
    DriveFile,
    DriveFileDownloadResponse,
    DriveFileListResponse,
)
from app.services.drive_client import download_file, list_files


router = APIRouter(
    prefix="/files",
    tags=["Google Drive"],
)


def _raise_drive_error(action: str, error: Exception):
    if isinstance(error, (TimeoutError, socket.timeout)):
        raise HTTPException(
            status_code=504,
            detail=f"Google Drive {action} timed out: {error}",
        ) from error

    if isinstance(error, RuntimeError) and "not connected" in str(error):
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    raise HTTPException(
        status_code=502,
        detail=f"Google Drive {action} failed: {error}",
    ) from error


@router.get(
    "",
    response_model=DriveFileListResponse,
)
def get_files(
    page_size: int = 50,
    page_token: str | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        result = list_files(
            db,
            user_id=user_id,
            page_size=page_size,
            page_token=page_token,
        )
    except Exception as error:
        _raise_drive_error("request", error)

    files = [
        DriveFile(
            id=file["id"],
            name=file["name"],
            mime_type=file["mimeType"],
            modified_time=file["modifiedTime"],
        )
        for file in result["files"]
    ]

    return DriveFileListResponse(
        files=files,
        count=len(files),
        next_page_token=result["next_page_token"],
    )


@router.get(
    "/{file_id}/download",
    response_model=DriveFileDownloadResponse,
)
def get_file_download(
    file_id: str,
    name: str,
    mime_type: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        raw_bytes = download_file(
            db,
            user_id=user_id,
            file_id=file_id,
        )
    except Exception as error:
        _raise_drive_error("download", error)

    encoded = base64.b64encode(raw_bytes).decode("utf-8")

    return DriveFileDownloadResponse(
        id=file_id,
        name=name,
        mime_type=mime_type,
        content_base64=encoded,
    )
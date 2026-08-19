import base64
import socket

from fastapi import FastAPI, HTTPException

from drive_client import list_files, download_file
from schemas import DriveFile, DriveFileListResponse, DriveFileDownloadResponse

app = FastAPI(title="Drive Service", version="1.0")


def _raise_drive_error(action: str, error: Exception):
    if isinstance(error, (TimeoutError, socket.timeout)):
        raise HTTPException(
            status_code=504,
            detail=f"Google Drive {action} timed out: {error}",
        ) from error

    raise HTTPException(
        status_code=502,
        detail=f"Google Drive {action} failed: {error}",
    ) from error


@app.get("/files", response_model=DriveFileListResponse)
def get_files(page_size: int = 50, page_token: str | None = None):
    """
    list files from google drive
    """
    try:
        result = list_files(page_size=page_size, page_token=page_token)
    except Exception as e:
        _raise_drive_error("request", e)

    files = [
        DriveFile(
            id=f["id"],
            name=f["name"],
            mime_type=f["mimeType"],
            modified_time=f["modifiedTime"],
        )
        for f in result["files"]
    ]

    return DriveFileListResponse(
        files=files,
        count=len(files),
        next_page_token=result["next_page_token"],
    )


@app.get("/files/{file_id}/download", response_model=DriveFileDownloadResponse)
def get_file_download(file_id: str, name: str, mime_type: str):
    """
    download files from google drive
    """
    try:
        raw_bytes = download_file(file_id)
    except Exception as e:
        _raise_drive_error("download", e)

    encoded = base64.b64encode(raw_bytes).decode("utf-8")

    return DriveFileDownloadResponse(
        id=file_id,
        name=name,
        mime_type=mime_type,
        content_base64=encoded,
    )

import base64
from fastapi import FastAPI, HTTPException
from drive_client import list_files, download_file
from schemas import DriveFile, DriveFileListResponse, DriveFileDownloadResponse

app = FastAPI(title="Drive Service",version="1.0")


@app.get("/files", response_model=DriveFileListResponse)
def get_files():
    """
    list files from google drive
    """
    raw_files = list_files()

    files = [
        DriveFile(
            id=f["id"],
            name=f["name"],
            mime_type=f["mimeType"],
            modified_time=f["modifiedTime"],
        )
        for f in raw_files
    ]

    return DriveFileListResponse(files=files, count=len(files))


@app.get("/files/{file_id}/download", response_model=DriveFileDownloadResponse)
def get_file_download(file_id: str, name: str, mime_type: str):
    """
    download files from google drive
    """
    try:
        raw_bytes = download_file(file_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File download failed: {str(e)}")

    encoded = base64.b64encode(raw_bytes).decode("utf-8")

    return DriveFileDownloadResponse(
        id=file_id,
        name=name,       
        mime_type=mime_type,  
        content_base64=encoded,
    )
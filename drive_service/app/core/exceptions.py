from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class DriveServiceError(Exception):
    """Base exception for drive service errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DriveFileNotFoundError(DriveServiceError):
    def __init__(self, file_id: str):
        super().__init__(f"Drive file not found: {file_id}", status_code=404)


class DriveAuthError(DriveServiceError):
    def __init__(self, message: str = "Google Drive authentication failed"):
        super().__init__(message, status_code=503)


async def drive_service_exception_handler(
    request: Request, exc: DriveServiceError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": detail},
    )

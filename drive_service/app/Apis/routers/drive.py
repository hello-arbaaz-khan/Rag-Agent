from __future__ import annotations

import base64
import logging
import os
import socket
from urllib.parse import urlencode

import requests as google_requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.core.auth import get_current_user_id
from app.core.crypto import decrypt_token, encrypt_token
from app.core.state import sign_state, store_state, verify_and_consume_state
from app.db.session import get_db
from app.models.google_drive_account import GoogleDriveAccount
from app.services.drive_client import download_file, list_files
from apps.documents.tasks import sync_google_drive_task
from app.Apis.schemas.drive import (
    DriveFile,
    DriveFileDownloadResponse,
    DriveFileListResponse,
    DriveSyncQueuedResponse,
)
import socket
from datetime import datetime
from urllib.parse import urlencode

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/drive",
    tags=["Google Drive"],
)


class DriveConnectResponse(BaseModel):
    connected: bool
    google_email: str


class DriveStatusResponse(BaseModel):
    connected: bool
    google_email: str | None = None
    connected_at: datetime | None = None


def _frontend_redirect(**params) -> RedirectResponse:
    base = settings.frontend_base_url.rstrip("/")
    url = f"{base}/drive/callback?{urlencode(params)}"
    return RedirectResponse(url=url, status_code=302)


def _build_flow() -> Flow:
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=settings.google_drive_scopes,
        redirect_uri=(
            f"{settings.drive_service_base_url}/api/v1/drive/callback"
        ),
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


# ---------------------------------------------------------------------------
# Google Drive OAuth
# ---------------------------------------------------------------------------


@router.get("/connect")
def connect(
    user_id: int = Depends(get_current_user_id),
):
    flow = _build_flow()

    state_token = sign_state(user_id)

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="select_account consent",
        state=state_token,
    )

    store_state(
        state_token,
        user_id,
        flow.code_verifier,
    )

    return {"auth_url": auth_url}

@router.get(
    "/status",
    response_model=DriveStatusResponse,
)
def drive_status(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    account = (
        db.query(GoogleDriveAccount)
        .filter_by(user_id=user_id)
        .first()
    )

    if account is None:
        return DriveStatusResponse(connected=False)

    return DriveStatusResponse(
        connected=True,
        google_email=account.google_email,
        connected_at=account.created_at,
    )

@router.get("/callback")
def callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    # Google returns an error when the user denies access.
    if error:
        return _frontend_redirect(
            drive_status="error",
            message=error,
        )

    if not code or not state:
        return _frontend_redirect(
            drive_status="error",
            message="Missing code or state from Google.",
        )

    try:
        data = verify_and_consume_state(state)
    except ValueError as exc:
        return _frontend_redirect(
            drive_status="error",
            message=str(exc),
        )

    user_id = data["user_id"]
    code_verifier = data["code_verifier"]

    flow = _build_flow()
    flow.code_verifier = code_verifier

    try:
        flow.fetch_token(code=code)
    except Exception as exc:
        logger.warning(
            "Failed to exchange code for user_id=%s: %s",
            user_id,
            exc,
        )

        return _frontend_redirect(
            drive_status="error",
            message="Failed to complete Google sign-in.",
        )

    creds = flow.credentials

    try:
        oauth2_service = build(
            "oauth2",
            "v2",
            credentials=creds,
            cache_discovery=False,
        )

        userinfo = (
            oauth2_service
            .userinfo()
            .get()
            .execute()
        )

    except Exception as exc:
        logger.warning(
            "Failed to fetch userinfo for user_id=%s: %s",
            user_id,
            exc,
        )

        return _frontend_redirect(
            drive_status="error",
            message="Failed to read Google account info.",
        )

    account = (
        db.query(GoogleDriveAccount)
        .filter_by(user_id=user_id)
        .first()
    )

    if account is None:
        account = GoogleDriveAccount(user_id=user_id)
        db.add(account)

    account.google_email = userinfo["email"]
    account.google_account_id = userinfo["id"]
    account.access_token_encrypted = encrypt_token(creds.token)
    account.refresh_token_encrypted = encrypt_token(creds.refresh_token)
    account.token_expiry = creds.expiry
    account.scopes = " ".join(creds.scopes)
    account.key_version = 1

    db.commit()

    try:
        sync_task = sync_google_drive_task.delay(user_id)
    except Exception:
        logger.exception(
            "Drive connected, but initial sync could not be queued "
            "for user_id=%s",
            user_id,
        )
        return _frontend_redirect(
            drive_status="error",
            message=(
                "Google Drive connected, but the initial sync could not "
                "be queued. Please try syncing again."
            ),
        )

    return _frontend_redirect(
        drive_status="connected",
        email=account.google_email,
        drive_sync_task_id=sync_task.id,
    )


@router.delete("/disconnect")
def disconnect(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    account = (
        db.query(GoogleDriveAccount)
        .filter_by(user_id=user_id)
        .first()
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Google Drive not connected for this user.",
        )

    try:
        refresh_token = decrypt_token(
            account.refresh_token_encrypted,
            account.key_version,
        )

        google_requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": refresh_token},
            timeout=10,
        )

    except Exception as exc:
        logger.warning(
            "Failed to revoke token with Google for user_id=%s: %s",
            user_id,
            exc,
        )

    db.delete(account)
    db.commit()

    return {"disconnected": True}


# ---------------------------------------------------------------------------
# Google Drive Files
# ---------------------------------------------------------------------------


@router.post(
    "/sync",
    response_model=DriveSyncQueuedResponse,
    status_code=202,
)
def sync_drive(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    account = db.query(GoogleDriveAccount).filter_by(user_id=user_id).first()
    if account is None:
        raise HTTPException(
            status_code=409,
            detail="Connect a Google Drive account before syncing.",
        )

    try:
        task = sync_google_drive_task.delay(user_id)
    except Exception as exc:
        logger.exception(
            "Failed to queue Drive sync for user_id=%s",
            user_id,
        )
        raise HTTPException(
            status_code=503,
            detail="Unable to queue Google Drive synchronization.",
        ) from exc

    return DriveSyncQueuedResponse(
        task_id=task.id,
        status="queued",
    )


@router.get(
    "/files",
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
    "/files/{file_id}/download",
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
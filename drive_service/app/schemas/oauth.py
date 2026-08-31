import os
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

from fastapi import APIRouter, Depends, HTTPException
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from pydantic import BaseModel
from sqlalchemy.orm import Session

import logging
import requests as google_requests

logger = logging.getLogger(__name__)
from app.config import settings
from app.db.session import get_db
from app.models.google_drive_account import GoogleDriveAccount
from app.core.crypto import encrypt_token
from app.core.state import sign_state, store_state, verify_and_consume_state
from app.core.auth import get_current_user_id

router = APIRouter()


class DriveConnectResponse(BaseModel):
    connected: bool
    google_email: str


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
        redirect_uri=f"{settings.drive_service_base_url}/callback",
    )


@router.get("/connect")
def connect(user_id: int = Depends(get_current_user_id)):
    flow = _build_flow()
    state_token = sign_state(user_id)

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="select_account consent",
        state=state_token,
    )

    store_state(state_token, user_id, flow.code_verifier)

    return {"auth_url": auth_url}


@router.get("/callback", response_model=DriveConnectResponse)
def callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        data = verify_and_consume_state(state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user_id = data["user_id"]
    code_verifier = data["code_verifier"]

    flow = _build_flow()
    flow.code_verifier = code_verifier

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {e}")

    creds = flow.credentials

    oauth2_service = build("oauth2", "v2", credentials=creds, cache_discovery=False)
    userinfo = oauth2_service.userinfo().get().execute()

    account = db.query(GoogleDriveAccount).filter_by(user_id=user_id).first()

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

    return DriveConnectResponse(connected=True, google_email=account.google_email)

@router.delete("/disconnect")
def disconnect(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    account = db.query(GoogleDriveAccount).filter_by(user_id=user_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Google Drive not connected for this user.")

    try:
        refresh_token = decrypt_token(account.refresh_token_encrypted, account.key_version)
        google_requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": refresh_token},
            timeout=10,
        )
    except Exception as e:
        logger.warning("Failed to revoke token with Google for user_id=%s: %s", user_id, e)

    db.delete(account)
    db.commit()

    return {"disconnected": True}
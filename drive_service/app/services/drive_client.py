from datetime import timezone
import socket
import io

import httplib2
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
from sqlalchemy.orm import Session

from app.config import settings
from app.models.google_drive_account import GoogleDriveAccount
from app.core.crypto import encrypt_token, decrypt_token

_original_getaddrinfo = socket.getaddrinfo

def _prefer_ipv4_for_google_apis():
    def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        results = _original_getaddrinfo(host, port, family, type, proto, flags)
        if host and host.endswith("googleapis.com"):
            results.sort(key=lambda item: 0 if item[0] == socket.AF_INET else 1)
        return results

    socket.getaddrinfo = getaddrinfo

if settings.google_api_prefer_ipv4:
    _prefer_ipv4_for_google_apis()


def get_credentials(db: Session, user_id: int) -> Credentials:
    account = db.query(GoogleDriveAccount).filter_by(user_id=user_id).first()
    if not account:
        raise RuntimeError("Google Drive not connected for this user.")

    access_token = decrypt_token(account.access_token_encrypted, account.key_version)
    refresh_token = decrypt_token(account.refresh_token_encrypted, account.key_version)

    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )

    expiry = account.token_expiry
    if expiry.tzinfo is not None:
        expiry = expiry.astimezone(timezone.utc).replace(tzinfo=None)
    creds.expiry = expiry

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

        account.access_token_encrypted = encrypt_token(creds.token, account.key_version)
        account.token_expiry = creds.expiry
        db.commit()

    return creds


def get_drive_service(db: Session, user_id: int):
    creds = get_credentials(db, user_id)
    http = AuthorizedHttp(creds, http=httplib2.Http(timeout=settings.google_api_timeout_seconds))
    return build('drive', 'v3', http=http, cache_discovery=False)


def list_files(db: Session, user_id: int, page_size: int = 50, page_token: str = None):
    service = get_drive_service(db, user_id)

    result = service.files().list(
        pageSize=page_size,
        pageToken=page_token,
        q="trashed=false",
        fields='nextPageToken, files(id,name,mimeType,modifiedTime,trashed)'
    ).execute()

    return {
        'files': result.get('files', []),
        'next_page_token': result.get('nextPageToken'),
    }


def download_file(db: Session, user_id: int, file_id: str) -> bytes:
    service = get_drive_service(db, user_id)
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    buffer.seek(0)
    return buffer.read()
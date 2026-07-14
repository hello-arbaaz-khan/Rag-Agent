import os
import io
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import settings

def get_credentials():
    """
    Load OAuth credentials from token.json and refresh if expired.

    IMPORTANT: This function will NEVER launch a browser/local server.
    flow.run_local_server() hangs forever in server or Django shell contexts.
    If no valid token exists, raise RuntimeError with clear instructions.
    To generate a fresh token, run: python auth.py  (from drive_service/)
    """
    creds = None

    if os.path.exists(settings.google_token_file):
        creds = Credentials.from_authorized_user_file(
            settings.google_token_file, settings.google_drive_scopes
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Attempt a silent refresh using the stored refresh_token
            try:
                creds.refresh(Request())
                # Persist the newly refreshed token so next call is instant
                with open(settings.google_token_file, 'w') as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                raise RuntimeError(
                    f"OAuth token refresh failed: {e}. "
                    "The refresh token may be expired (Google 'Testing' mode "
                    "refresh tokens expire after 7 days). "
                    "Re-authenticate by running:  python auth.py  "
                    "inside the drive_service/ directory."
                ) from e
        else:
            # No token file, or token has no refresh_token at all.
            # We CANNOT call flow.run_local_server() here — it would hang forever
            # waiting for a browser callback that will never arrive in a server context.
            raise RuntimeError(
                "No valid OAuth token found. "
                "Run:  python auth.py  inside the drive_service/ directory "
                "to complete the one-time browser authentication, then restart "
                "the FastAPI service."
            )

    return creds


def get_drive_service():
    creds = get_credentials()
    return build('drive','v3',credentials=creds)

def list_files(pageSize: int=100):
    service = get_drive_service()
    result = service.files().list(pageSize=pageSize,fields='files(id,name,mimeType,modifiedTime)').execute()
    return result.get('files',[])


def download_file(file_id:str) -> bytes:
    """Download google drive file as bytes"""
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done=False
    while not done:
        status,done = downloader.next_chunk()
    buffer.seek(0)
    return buffer.read()
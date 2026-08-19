import os
import socket
import httplib2
import io
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp

from config import settings

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


def get_credentials():
    creds = None

    if os.path.exists(settings.google_token_file):
        creds = Credentials.from_authorized_user_file(
            settings.google_token_file, settings.google_drive_scopes
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(settings.google_token_file, 'w') as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                raise RuntimeError(
                    f"OAuth token refresh failed: {e}. "
                    "Re-authenticate by running: python auth.py "
                    "inside the drive_service/ directory."
                ) from e
        else:
            raise RuntimeError(
                "No valid OAuth token found. "
                "Run: python auth.py inside the drive_service/ directory."
            )

    return creds


def get_drive_service():
    creds = get_credentials()
    http = AuthorizedHttp(creds, http=httplib2.Http(timeout=settings.google_api_timeout_seconds))
    return build('drive', 'v3', http=http, cache_discovery=False)


def list_files(page_size: int = 50, page_token: str = None):
    service = get_drive_service()
    
    # IMPORTANT: q="trashed=false" only active files 
    # Trash deleted files will not be show 
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


def download_file(file_id: str) -> bytes:
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    buffer.seek(0)
    return buffer.read()
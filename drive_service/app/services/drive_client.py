import base64
import io
from datetime import datetime
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from app.config import settings
from app.core.exceptions import DriveAuthError, DriveFileNotFoundError, DriveServiceError
from app.schemas.drive import DriveFile


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class DriveClient:
    """Google Drive API client for listing and downloading files."""

    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service is not None:
            return self._service

        credentials_path = Path(settings.google_credentials_file)
        if not credentials_path.exists():
            raise DriveAuthError(
                f"Credentials file not found: {settings.google_credentials_file}"
            )

        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(credentials_path),
                scopes=SCOPES,
            )
            self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)
            return self._service
        except Exception as exc:
            raise DriveAuthError(str(exc)) from exc

    def _parse_file(self, item: dict) -> DriveFile:
        modified_at = None
        if item.get("modifiedTime"):
            modified_at = datetime.fromisoformat(item["modifiedTime"].replace("Z", "+00:00"))

        return DriveFile(
            id=item["id"],
            name=item.get("name", ""),
            mime_type=item.get("mimeType", ""),
            modified_at=modified_at,
            size=int(item["size"]) if item.get("size") else None,
            web_view_link=item.get("webViewLink"),
        )

    def _build_query(self) -> str:
        mime_filters = " or ".join(
            f"mimeType='{mime}'" for mime in settings.mime_type_list
        )
        query_parts = [f"({mime_filters})", "trashed=false"]

        if settings.google_drive_folder_id:
            query_parts.append(
                f"'{settings.google_drive_folder_id}' in parents"
            )

        return " and ".join(query_parts)

    def list_files(self, page_size: int = 50) -> list[DriveFile]:
        service = self._get_service()

        try:
            response = (
                service.files()
                .list(
                    q=self._build_query(),
                    pageSize=page_size,
                    fields=(
                        "files(id,name,mimeType,modifiedTime,size,webViewLink),"
                        "nextPageToken"
                    ),
                    orderBy="modifiedTime desc",
                )
                .execute()
            )
        except HttpError as exc:
            raise DriveServiceError(f"Failed to list Drive files: {exc}", status_code=502) from exc

        return [self._parse_file(item) for item in response.get("files", [])]

    def get_file(self, file_id: str) -> DriveFile:
        service = self._get_service()

        try:
            item = (
                service.files()
                .get(
                    fileId=file_id,
                    fields="id,name,mimeType,modifiedTime,size,webViewLink",
                )
                .execute()
            )
        except HttpError as exc:
            if exc.resp.status == 404:
                raise DriveFileNotFoundError(file_id) from exc
            raise DriveServiceError(f"Failed to fetch Drive file: {exc}", status_code=502) from exc

        return self._parse_file(item)

    def download_file(self, file_id: str) -> tuple[DriveFile, bytes]:
        service = self._get_service()
        metadata = self.get_file(file_id)

        try:
            request = service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

            return metadata, buffer.getvalue()
        except HttpError as exc:
            if exc.resp.status == 404:
                raise DriveFileNotFoundError(file_id) from exc
            raise DriveServiceError(f"Failed to download Drive file: {exc}", status_code=502) from exc

    def download_file_base64(self, file_id: str) -> tuple[DriveFile, str]:
        metadata, content = self.download_file(file_id)
        return metadata, base64.b64encode(content).decode("utf-8")


drive_client = DriveClient()

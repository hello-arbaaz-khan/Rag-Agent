from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import transaction
from googleapiclient.errors import HttpError

from apps.documents.models import UploadedDocument
from apps.documents.tasks import process_document_task

from ..db.session import SessionLocal
from .drive_client import (
    download_file_with_service,
    export_file_with_service,
    get_drive_service,
    list_all_files,
)


logger = logging.getLogger(__name__)

GOOGLE_WORKSPACE_EXPORTS = {
    "application/vnd.google-apps.document": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "docx",
    ),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx",
    ),
    "application/vnd.google-apps.presentation": ("application/pdf", "pdf"),
}

SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "text/plain": "txt",
    "text/csv": "csv",
    "text/markdown": "md",
    "text/html": "html",
    "application/xml": "xml",
    "text/xml": "xml",
    "application/epub+zip": "epub",
    "application/json": "json",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/tiff": "tiff",
}

MAX_WORKSPACE_EXPORT_BYTES = 10 * 1024 * 1024
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


class WorkspaceExportTooLarge(Exception):
    pass


def _filename(name: str, extension: str) -> str:
    base_name = Path(name).name
    suffix = f".{extension}"
    if not base_name.casefold().endswith(suffix):
        base_name = Path(base_name).stem
    return f"{base_name[:255 - len(suffix)]}{suffix}"


def _download_content(service, file: dict, file_type: str) -> bytes:
    mime_type = file["mimeType"]
    workspace_export = GOOGLE_WORKSPACE_EXPORTS.get(mime_type)

    if workspace_export:
        export_mime_type, extension = workspace_export
        if file_type != extension:
            raise ValueError(f"Unsupported export type for {mime_type}.")
        content = export_file_with_service(
            service,
            file["id"],
            export_mime_type,
        )
        if len(content) > MAX_WORKSPACE_EXPORT_BYTES:
            raise WorkspaceExportTooLarge(
                "Google Workspace exports are limited to 10 MB."
            )
        return content

    return download_file_with_service(service, file["id"])


def _is_export_size_limit_error(exc: HttpError) -> bool:
    return b"exportSizeLimitExceeded" in (exc.content or b"")


def sync_google_drive(user_id: int) -> dict[str, int]:
    """Import a user's supported Drive files into the existing document pipeline."""
    created = updated = unchanged = skipped = queued = 0

    with SessionLocal() as db:
        service = get_drive_service(db, user_id)
        files = list_all_files(
            db,
            user_id,
            service=service,
        )

        for drive_file in files:
            mime_type = drive_file.get("mimeType")
            if (
                drive_file.get("trashed")
                or mime_type == FOLDER_MIME_TYPE
            ):
                skipped += 1
                continue

            workspace_export = GOOGLE_WORKSPACE_EXPORTS.get(mime_type)
            file_type = (
                workspace_export[1]
                if workspace_export
                else SUPPORTED_MIME_TYPES.get(mime_type)
            )
            if file_type is None:
                skipped += 1
                continue

            try:
                content = _download_content(
                    service,
                    drive_file,
                    file_type,
                )
            except WorkspaceExportTooLarge:
                logger.warning(
                    "Skipping oversized Google Workspace export "
                    "file_id=%s user_id=%s",
                    drive_file["id"],
                    user_id,
                )
                skipped += 1
                continue
            except HttpError as exc:
                if workspace_export and _is_export_size_limit_error(exc):
                    logger.warning(
                        "Skipping oversized Google Workspace export "
                        "file_id=%s user_id=%s",
                        drive_file["id"],
                        user_id,
                    )
                    skipped += 1
                    continue
                raise

            if not content:
                logger.warning(
                    "Skipping empty Drive file file_id=%s user_id=%s",
                    drive_file["id"],
                    user_id,
                )
                skipped += 1
                continue

            file_hash = hashlib.sha256(content).hexdigest()
            name = _filename(drive_file["name"], file_type)
            old_file_name = None
            needs_processing = False

            with transaction.atomic():
                document = (
                    UploadedDocument.objects.select_for_update()
                    .filter(
                        user_id=user_id,
                        google_drive_file_id=drive_file["id"],
                    )
                    .first()
                )

                if document is None:
                    document = UploadedDocument(
                        user_id=user_id,
                        name=name,
                        file_type=file_type,
                        source=UploadedDocument.Source.GOOGLE_DRIVE,
                        google_drive_file_id=drive_file["id"],
                        file_size=len(content),
                        file_hash=file_hash,
                    )
                    changed = True
                    created += 1
                else:
                    changed = document.file_hash != file_hash
                    document.name = name
                    document.file_type = file_type
                    document.source = UploadedDocument.Source.GOOGLE_DRIVE
                    document.file_size = len(content)

                    if changed:
                        old_file_name = document.file.name
                        document.file_hash = file_hash
                        document.is_processed = False
                        document.processing_started_at = None
                        document.processing_error = None
                        updated += 1
                    elif (
                        not document.is_processed
                        and document.processing_error
                    ):
                        needs_processing = True
                    else:
                        unchanged += 1

                if changed:
                    document.file.save(
                        name,
                        ContentFile(content),
                        save=False,
                    )
                    document.save()
                    needs_processing = True
                elif not document._state.adding:
                    document.save(update_fields=["name", "file_type", "file_size", "updated_at"])

            if old_file_name and old_file_name != document.file.name:
                document.file.storage.delete(old_file_name)

            if needs_processing:
                try:
                    process_document_task.delay(document.id)
                except Exception as exc:
                    document.processing_error = (
                        "Failed to queue Drive document processing."
                    )
                    document.save(
                        update_fields=["processing_error", "updated_at"]
                    )
                    raise RuntimeError(
                        "Drive file was saved but document processing "
                        f"could not be queued (document_id={document.id})."
                    ) from exc
                queued += 1

    return {
        "total": len(files),
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "skipped": skipped,
        "queued_for_processing": queued,
    }

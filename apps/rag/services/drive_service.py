from datetime import datetime
import logging
import base64
import requests
from django.utils.dateparse import parse_datetime
from django.conf import settings
from django.core.files.base import ContentFile

from apps.rag.services.document_service import DocumentService
from apps.rag.models import DriveDocument

logger = logging.getLogger(__name__)

def _parse_modified_time(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return parse_datetime(value)
    return None

DRIVE_SERVICE_BASE_URL = getattr(settings, "DRIVE_SERVICE_BASE_URL", "http://127.0.0.1:8001")

MIME_TO_FILE_TYPE = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}


def fetch_drive_files(user):

    headers = {"Authorization": f"Bearer {get_jwt_for(user)}"}  # depends on Phase II's token-passing design — placeholder until then
    response = requests.get(f"{DRIVE_SERVICE_BASE_URL}/files/", headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get('files', [])

def fetch_drive_files_page(page_size=50, page_token=None):
    params = {"page_size": page_size}
    if page_token:
        params["page_token"] = page_token
    response = requests.get(f"{DRIVE_SERVICE_BASE_URL}/files", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def process_pending_drive_file(drive_doc_id: int, user):
    drive_doc = DriveDocument.objects.get(id=drive_doc_id, user=user)

    # Guard: skip if already picked up
    if drive_doc.sync_status not in ("pending", "failed"):
        logger.info("[drive] Skipping %s — status is '%s'", drive_doc.name, drive_doc.sync_status)
        return

    # Extra guard: if file is removed from Drive, skip it
    if drive_doc.sync_status == "removed":
        logger.info("[drive] Skipping %s — removed from Drive", drive_doc.name)
        return

    drive_doc.sync_status = "processing"
    drive_doc.sync_error = None
    drive_doc.save()

    logger.info("[drive] Starting processing for: %s (id=%s)", drive_doc.name, drive_doc_id)
    
    try:
        response = requests.get(
            f"{DRIVE_SERVICE_BASE_URL}/files/{drive_doc.drive_file_id}/download",
            params={"name": drive_doc.name, "mime_type": drive_doc.mime_type},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        file_bytes = base64.b64decode(data["content_base64"])
        django_file = ContentFile(file_bytes, name=drive_doc.name)

        file_type = MIME_TO_FILE_TYPE.get(drive_doc.mime_type)
        if not file_type:
            raise ValueError(f"Unsupported file type: {drive_doc.mime_type}")

        uploaded_doc = DocumentService.create_and_process(
            user=user,
            file=django_file,
            name=drive_doc.name,
            file_type=file_type,
        )

        drive_doc.document = uploaded_doc
        drive_doc.sync_status = "indexed"
        drive_doc.sync_error = None
        drive_doc.save()

    except Exception as e:
        logger.error("[drive] Failed processing %s: %s", drive_doc.name, repr(e))
        drive_doc.sync_status = "failed"
        drive_doc.sync_error = repr(e)
        drive_doc.save()


def sync_drive_documents(user):
    """Sync drive documents to local database. Clean up files deleted from Drive."""
    files = fetch_drive_files(user)
    active_drive_ids = {f['id'] for f in files if not f.get('trashed', False)}
    created_count = 0
    updated_count = 0
    removed_count = 0
    pending_ids = []

    # Step 1: Active files sync
    for f in files:
        if f.get('trashed', False):
            continue

        drive_modified = _parse_modified_time(f.get('modified_time'))

        obj, created = DriveDocument.objects.get_or_create(
            drive_file_id=f['id'],
            user=user,
            defaults={
                "name": f['name'],
                "mime_type": f['mime_type'],
                "drive_modified_at": drive_modified,
                "sync_status": "pending",
            }
        )

        if created:
            created_count += 1
            pending_ids.append(obj.id)
        else:
            new_modified = _parse_modified_time(f.get('modified_time'))
            obj_modified = obj.drive_modified_at

            if (new_modified and obj_modified and 
                isinstance(obj_modified, datetime) and 
                new_modified > obj_modified):
                if obj.sync_status == "indexed":
                    obj.drive_modified_at = new_modified
                    obj.sync_status = "pending"
                    obj.sync_error = None
                    obj.save()
                    updated_count += 1
                    pending_ids.append(obj.id)
            elif obj.sync_status in ("pending", "failed"):
                pending_ids.append(obj.id)

    # Step 2: Remove files that are no longer in Drive    
    # (permanently deleted or moved to trash)
    orphaned = DriveDocument.objects.filter(user=user).exclude(drive_file_id__in=active_drive_ids)    
    for drive_doc in orphaned:
        logger.info("[drive] File removed from Drive: %s", drive_doc.name)
        drive_doc.delete()
        removed_count += 1

    # Step 3: Pending files processing
    for doc_id in pending_ids:
        try:
            process_pending_drive_file(doc_id, user)
        except Exception as e:
            logger.error("[drive] Error processing pending file %s: %s", doc_id, e)

    return {
        "total_files": len(files),
        "created": created_count,
        "updated": updated_count,
        "removed": removed_count,
        "queued_for_processing": len(pending_ids),
    }


def _serialize_drive_doc(doc):
    return {
        "id": doc.id,
        "drive_file_id": doc.drive_file_id,
        "name": doc.name,
        "mime_type": doc.mime_type,
        "drive_modified_at": doc.drive_modified_at,
        "sync_status": doc.sync_status,
        "document_id": doc.document_id,
    }


SYNC_STATUS_ORDER = {"indexed": 0, "processing": 1, "pending": 2, "failed": 3}

def browse_files(user, page_token=None, page_size=50):
    """
    Page of files for the search/browse UI.
    Removed/deleted files are automatically excluded because
    sync_drive_documents() deletes them from local DB.
    """
    if page_token is None:
        local_files = list(DriveDocument.objects.filter(user=user))
        local_files.sort(key=lambda d: (SYNC_STATUS_ORDER.get(d.sync_status, 9), d.name.lower()))
        total_local = len(local_files)

        if total_local >= page_size:
            return {
                "files": [_serialize_drive_doc(d) for d in local_files[:page_size]],
                "next_page_token": "__DRIVE_START__",
                "has_more": True,
            }

        remaining_slots = page_size - total_local
        drive_result = fetch_drive_files_page(page_size=page_size)
        known_ids = {d.drive_file_id for d in local_files}
        new_from_drive = [f for f in drive_result["files"] if f["id"] not in known_ids]

        extra_docs = []
        for f in new_from_drive[:remaining_slots]:
            if f.get('trashed', False):
                continue
            drive_modified = _parse_modified_time(f.get('modified_time'))
            obj, _ = DriveDocument.objects.get_or_create(
                drive_file_id=f["id"],
                defaults={
                    "name": f["name"],
                    "mime_type": f["mime_type"],
                    "drive_modified_at": drive_modified,
                    "sync_status": "pending",
                    "user": user,
                },
            )
            extra_docs.append(obj)

        more_in_drive = len(new_from_drive) > remaining_slots or drive_result["next_page_token"] is not None
        combined = local_files + extra_docs
        return {
            "files": [_serialize_drive_doc(d) for d in combined],
            "next_page_token": drive_result["next_page_token"] if more_in_drive else None,
            "has_more": more_in_drive,
        }

    # "See more" clicked
    real_token = None if page_token == "__DRIVE_START__" else page_token
    drive_result = fetch_drive_files_page(page_size=page_size, page_token=real_token)

    batch_docs = []
    for f in drive_result["files"]:
        if f.get('trashed', False):
            continue
        drive_modified = _parse_modified_time(f.get('modified_time'))
        obj, _ = DriveDocument.objects.get_or_create(
            drive_file_id=f["id"],
            defaults={
                "name": f["name"],
                "mime_type": f["mime_type"],
                "drive_modified_at": drive_modified,
                "sync_status": "pending",
            },
        )
        batch_docs.append(obj)

    return {
        "files": [_serialize_drive_doc(d) for d in batch_docs],
        "next_page_token": drive_result["next_page_token"],
        "has_more": drive_result["next_page_token"] is not None,
    }
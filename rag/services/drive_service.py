from django.core.files.base import ContentFile
from rag.services.document_service import DocumentService
import base64
from rag.models import DriveDocument
import requests
from django.conf import settings


DRIVE_SERVICE_BASE_URL = getattr(settings, "DRIVE_SERVICE_BASE_URL", "http://127.0.0.1:8001")

MIME_TO_FILE_TYPE = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "video/mp4": "mp4",
}

def fetch_drive_files():
    response = requests.get(f"{DRIVE_SERVICE_BASE_URL}/files/", timeout=30)
    response.raise_for_status()
    data = response.json()
    return data['files']

def process_pending_drive_file(drive_doc_id: int):
    """ Process and download drive document """
    drive_doc = DriveDocument.objects.get(id=drive_doc_id)

    # Guard: skip if another call already picked this document up
    if drive_doc.sync_status not in ("pending", "failed"):
        print(f"[drive] Skipping {drive_doc.name} — status is already '{drive_doc.sync_status}'")
        return

    # Mark as processing immediately to prevent double-queuing on concurrent sync calls
    drive_doc.sync_status = "processing"
    drive_doc.sync_error = None
    drive_doc.save()

    print(f"[drive] Starting processing for: {drive_doc.name} (id={drive_doc_id})", flush=True)
    try:
        print(f"[drive] → Downloading from FastAPI: {DRIVE_SERVICE_BASE_URL}/files/{drive_doc.drive_file_id}/download", flush=True)
        response = requests.get(
            f"{DRIVE_SERVICE_BASE_URL}/files/{drive_doc.drive_file_id}/download",
            params={"name": drive_doc.name, "mime_type": drive_doc.mime_type},
            timeout=120,  # large PDFs can take time; fail clearly instead of hanging forever
        )
        print(f"[drive] → Download response: HTTP {response.status_code}", flush=True)

        response.raise_for_status()
        data = response.json()
        file_bytes = base64.b64decode(data["content_base64"])
        django_file = ContentFile(file_bytes, name=drive_doc.name)

        file_type = MIME_TO_FILE_TYPE.get(drive_doc.mime_type)
        if not file_type:
            raise ValueError(f"Unsupported file type: {drive_doc.mime_type}")

        print(f"[drive] → Kicking off background processing for {drive_doc.name}", flush=True)
        uploaded_doc = DocumentService.create_and_process(
            file=django_file,
            name=drive_doc.name,
            file_type=file_type,
        )
        print(f"[drive] → Document queued (id={uploaded_doc.id}); background thread will process it.", flush=True)

        drive_doc.document = uploaded_doc
        drive_doc.sync_status = "indexed"
        drive_doc.sync_error = None
        drive_doc.save()

    except Exception as e:
        print(f"[drive] ✗ Failed processing {drive_doc.name}: {repr(e)}", flush=True)
        drive_doc.sync_status = "failed"
        drive_doc.sync_error = repr(e)  # repr captures the exception class, str() often gives empty string
        drive_doc.save()


def sync_drive_documents():
    """ Sync drive documents to local database """
    files = fetch_drive_files()
    created_count = 0
    updated_count = 0
    pending_ids = []

    for f in files:
        obj, created = DriveDocument.objects.get_or_create(
            drive_file_id=f['id'],
            defaults={
                "name": f['name'],
                "mime_type": f['mime_type'],
                "drive_modified_at": f['modified_time'],
            }
        )

        if created:
            created_count += 1
        else:
            updated_count += 1
            # Re-queue if the file was modified in Drive since last sync
            if str(obj.drive_modified_at) != str(f['modified_time']) and obj.sync_status == "indexed":
                obj.drive_modified_at = f['modified_time']
                obj.sync_status = "pending"
                obj.save()

        # Only queue docs that are pending (not currently processing/already indexed)
        if obj.sync_status == "pending":
            pending_ids.append(obj.id)

    for doc_id in pending_ids:
        process_pending_drive_file(doc_id)

    return {
        "total_files": len(files),
        "created": created_count,
        "updated": updated_count,
        "queued_for_processing": len(pending_ids),
    }

def fetch_drive_files_page(page_size=50, page_token=None):
    """Fetch one page of files from the FastAPI drive service."""
    params = {"page_size": page_size}
    if page_token:
        params["page_token"] = page_token
    response = requests.get(f"{DRIVE_SERVICE_BASE_URL}/files", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


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


def browse_files(page_token=None, page_size=50):
    """
    Page of files for the search/browse UI — combines local DriveDocument rows
    with live Google Drive data, following the confirmed rule:
    if total files <= page_size, show everything at once; otherwise show local
    DB rows first, and use 'See more' to pull live batches from Drive.
    """
    if page_token is None:
        local_files = list(DriveDocument.objects.all())
        local_files.sort(key=lambda d: (SYNC_STATUS_ORDER.get(d.sync_status, 9), d.name.lower()))
        total_local = len(local_files)

        if total_local >= page_size:
            return {
                "files": [_serialize_drive_doc(d) for d in local_files[:page_size]],
                "next_page_token": "__DRIVE_START__",  # next click starts live Drive pagination
                "has_more": True,
            }

        # Fewer local files than a full page — check live Drive to fill the gap
        remaining_slots = page_size - total_local
        drive_result = fetch_drive_files_page(page_size=page_size)
        known_ids = {d.drive_file_id for d in local_files}
        new_from_drive = [f for f in drive_result["files"] if f["id"] not in known_ids]

        extra_docs = []
        for f in new_from_drive[:remaining_slots]:
            obj, _ = DriveDocument.objects.get_or_create(
                drive_file_id=f["id"],
                defaults={
                    "name": f["name"],
                    "mime_type": f["mime_type"],
                    "drive_modified_at": f["modified_time"],
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

    # "See more" clicked — page_token is a live Drive page token
    real_token = None if page_token == "__DRIVE_START__" else page_token
    drive_result = fetch_drive_files_page(page_size=page_size, page_token=real_token)

    batch_docs = []
    for f in drive_result["files"]:
        obj, _ = DriveDocument.objects.get_or_create(
            drive_file_id=f["id"],
            defaults={
                "name": f["name"],
                "mime_type": f["mime_type"],
                "drive_modified_at": f["modified_time"],
            },
        )
        batch_docs.append(obj)

    return {
        "files": [_serialize_drive_doc(d) for d in batch_docs],
        "next_page_token": drive_result["next_page_token"],
        "has_more": drive_result["next_page_token"] is not None,
    }
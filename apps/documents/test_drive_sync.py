from __future__ import annotations

import hashlib
from contextlib import ExitStack
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.documents.models import UploadedDocument
from drive_service.app.services import drive_sync


User = get_user_model()


class GoogleDriveSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="drive-sync@example.com",
            password="test-password",
        )
        self.file = {
            "id": "drive-file-1",
            "name": "notes.txt",
            "mimeType": "text/plain",
            "modifiedTime": "2026-10-05T10:00:00Z",
        }
        self.content = b"First version of a document."
        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)
        self.media_settings = override_settings(
            MEDIA_ROOT=self.temp_media.name,
        )
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)

        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.session = MagicMock()
        session_factory = self.stack.enter_context(
            patch.object(drive_sync, "SessionLocal")
        )
        session_factory.return_value.__enter__.return_value = self.session
        self.drive_service = object()
        self.stack.enter_context(
            patch.object(
                drive_sync,
                "get_drive_service",
                return_value=self.drive_service,
            )
        )
        self.list_files = self.stack.enter_context(
            patch.object(
                drive_sync,
                "list_all_files",
                return_value=[self.file],
            )
        )
        self.download = self.stack.enter_context(
            patch.object(
                drive_sync,
                "download_file_with_service",
                side_effect=lambda _service, _file_id: self.content,
            )
        )
        self.export = self.stack.enter_context(
            patch.object(drive_sync, "export_file_with_service")
        )
        self.process_task = self.stack.enter_context(
            patch.object(drive_sync.process_document_task, "delay")
        )
        self.process_task.return_value.id = "process-task-id"

    def test_sync_imports_supported_file_once_and_skips_unchanged_reprocessing(self):
        first = drive_sync.sync_google_drive(self.user.pk)

        document = UploadedDocument.objects.get(
            user=self.user,
            google_drive_file_id=self.file["id"],
        )
        self.assertEqual(first["created"], 1)
        self.assertEqual(first["queued_for_processing"], 1)
        self.assertEqual(document.source, UploadedDocument.Source.GOOGLE_DRIVE)
        self.assertEqual(document.file_type, "txt")
        self.assertEqual(document.file_size, len(self.content))
        self.assertEqual(
            document.file_hash,
            hashlib.sha256(self.content).hexdigest(),
        )
        with document.file.open("rb") as stored:
            self.assertEqual(stored.read(), self.content)

        second = drive_sync.sync_google_drive(self.user.pk)
        self.assertEqual(second["unchanged"], 1)
        self.assertEqual(second["queued_for_processing"], 0)
        self.assertEqual(
            UploadedDocument.objects.filter(
                user=self.user,
                google_drive_file_id=self.file["id"],
            ).count(),
            1,
        )
        self.process_task.assert_called_once_with(document.pk)
        self.assertEqual(self.download.call_count, 2)

    def test_changed_content_updates_existing_document_and_queues_reprocessing(self):
        drive_sync.sync_google_drive(self.user.pk)
        document = UploadedDocument.objects.get(
            user=self.user,
            google_drive_file_id=self.file["id"],
        )
        document.is_processed = True
        document.save(update_fields=["is_processed"])
        original_id = document.pk

        self.content = b"Updated content."
        result = drive_sync.sync_google_drive(self.user.pk)

        document.refresh_from_db()
        self.assertEqual(result["updated"], 1)
        self.assertEqual(document.pk, original_id)
        self.assertFalse(document.is_processed)
        with document.file.open("rb") as stored:
            self.assertEqual(stored.read(), self.content)
        self.assertEqual(self.process_task.call_count, 2)

    def test_unsupported_files_and_folders_are_skipped(self):
        self.list_files.return_value = [
            {**self.file, "mimeType": "application/vnd.google-apps.folder"},
            {**self.file, "id": "unsupported", "mimeType": "application/zip"},
        ]

        result = drive_sync.sync_google_drive(self.user.pk)

        self.assertEqual(result["skipped"], 2)
        self.assertEqual(result["created"], 0)
        self.assertFalse(UploadedDocument.objects.exists())
        self.download.assert_not_called()
        self.process_task.assert_not_called()

    def test_same_drive_file_id_is_scoped_to_each_user(self):
        drive_sync.sync_google_drive(self.user.pk)
        another_user = User.objects.create_user(
            email="other-drive-sync@example.com",
            password="test-password",
        )

        drive_sync.sync_google_drive(another_user.pk)

        self.assertEqual(
            UploadedDocument.objects.filter(
                google_drive_file_id=self.file["id"],
            ).count(),
            2,
        )
        self.assertEqual(
            UploadedDocument.objects.filter(user=self.user).count(),
            1,
        )
        self.assertEqual(
            UploadedDocument.objects.filter(user=another_user).count(),
            1,
        )

    def test_google_workspace_document_is_exported_as_supported_docx(self):
        self.list_files.return_value = [
            {
                **self.file,
                "name": "Google document",
                "mimeType": "application/vnd.google-apps.document",
            },
        ]
        self.export.return_value = b"exported docx content"

        result = drive_sync.sync_google_drive(self.user.pk)

        document = UploadedDocument.objects.get(
            google_drive_file_id=self.file["id"],
        )
        self.assertEqual(result["created"], 1)
        self.assertEqual(document.file_type, "docx")
        self.assertEqual(document.name, "Google document.docx")
        self.export.assert_called_once_with(
            self.drive_service,
            self.file["id"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.download.assert_not_called()

    def test_oversized_workspace_export_is_skipped(self):
        self.list_files.return_value = [
            {
                **self.file,
                "name": "Google document",
                "mimeType": "application/vnd.google-apps.document",
            },
        ]
        self.export.return_value = (
            b"x" * (drive_sync.MAX_WORKSPACE_EXPORT_BYTES + 1)
        )

        result = drive_sync.sync_google_drive(self.user.pk)

        self.assertEqual(result["skipped"], 1)
        self.assertFalse(UploadedDocument.objects.exists())
        self.process_task.assert_not_called()

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from apps.backups.services import run_backup


def test_drive_upload_when_drive_flag_enabled(backup_settings, sqlite_db, fake_drive):
    backup_settings.BACKUP_GOOGLE_DRIVE_ENABLED = True
    report = run_backup()
    assert report.ok and report.drive_link == "https://drive/x"
    kwargs = fake_drive.files.return_value.create.call_args.kwargs
    assert kwargs["body"]["parents"] == ["folder-123"]
    assert kwargs["body"]["name"] == report.path.name
    assert kwargs["supportsAllDrives"] is True and kwargs["media_body"] == "media"


def test_drive_not_called_when_drive_flag_disabled(backup_settings, sqlite_db, fake_drive):
    run_backup()
    fake_drive.files.assert_not_called()


def test_both_destinations_enabled_email_contains_drive_link(
    backup_settings, sqlite_db, fake_drive, mailoutbox
):
    backup_settings.BACKUP_GOOGLE_DRIVE_ENABLED = True
    backup_settings.BACKUP_EMAIL_ENABLED = True
    report = run_backup()
    assert report.ok
    assert "https://drive/x" in mailoutbox[0].body


def test_drive_failure_still_sends_email_and_exits_non_zero(
    backup_settings, sqlite_db, fake_drive, mailoutbox
):
    from django.core.management import call_command
    from django.core.management.base import CommandError

    backup_settings.BACKUP_GOOGLE_DRIVE_ENABLED = True
    backup_settings.BACKUP_EMAIL_ENABLED = True
    fake_drive.files.return_value.create.return_value.next_chunk.side_effect = PermissionError("x")
    err = Exception("denied")
    err.resp = MagicMock(status=403)
    fake_drive.files.return_value.create.return_value.next_chunk.side_effect = err
    with pytest.raises(CommandError, match="google_drive"):
        call_command("backup_db")
    assert len(mailoutbox) == 1 and "Drive upload FAILED" in mailoutbox[0].body
    assert len(list(__import__("pathlib").Path(backup_settings.BACKUP_DIR).iterdir())) == 1


def test_transient_errors_retried_but_auth_errors_not(backup_settings, sqlite_db, fake_drive):
    backup_settings.BACKUP_GOOGLE_DRIVE_ENABLED = True
    request = fake_drive.files.return_value.create.return_value
    transient = Exception("busy")
    transient.resp = MagicMock(status=503)
    request.next_chunk.side_effect = [transient, transient, (None, {"id": "1", "webViewLink": "l"})]
    assert run_backup().ok
    assert request.next_chunk.call_count == 3

    request.next_chunk.reset_mock()
    forbidden = Exception("no")
    forbidden.resp = MagicMock(status=403)
    request.next_chunk.side_effect = forbidden
    assert not run_backup().ok
    assert request.next_chunk.call_count == 1  # 4xx: never retried

    request.next_chunk.reset_mock()
    request.next_chunk.side_effect = ConnectionError("down")
    assert not run_backup().ok
    assert request.next_chunk.call_count == 3  # network: max 3 attempts


def test_drive_retention_deletes_only_prefixed_old_files(backup_settings, sqlite_db, fake_drive):
    backup_settings.BACKUP_GOOGLE_DRIVE_ENABLED = True
    now = datetime.now(UTC)
    old, recent = (now - timedelta(days=60)).isoformat(), (now - timedelta(days=1)).isoformat()
    fake_drive.files.return_value.list.return_value.execute.return_value = {
        "files": [
            {"id": "a", "name": "db-backup-1.dump", "createdTime": old},
            {"id": "b", "name": "db-backup-2.dump", "createdTime": recent},
            {"id": "c", "name": "photos.zip", "createdTime": old},
        ]
    }
    assert run_backup().ok
    deleted = [c.kwargs["fileId"] for c in fake_drive.files.return_value.delete.call_args_list]
    assert deleted == ["a"]


def test_drive_retention_zero_disables_remote_cleanup(backup_settings, sqlite_db, fake_drive):
    backup_settings.BACKUP_GOOGLE_DRIVE_ENABLED = True
    backup_settings.GOOGLE_DRIVE_RETENTION_DAYS = 0
    run_backup()
    fake_drive.files.return_value.list.assert_not_called()

import gzip
import os
import sqlite3
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from apps.backups import services
from apps.backups.services import BackupConfigError, BackupError, run_backup


def test_sqlite_backup_creates_valid_compressed_file(backup_settings, sqlite_db, tmp_path):
    path = services.create_backup()
    assert path.name.startswith("db-backup-") and path.name.endswith(".sqlite3.gz")
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    restored = tmp_path / "restored.sqlite3"
    restored.write_bytes(gzip.decompress(path.read_bytes()))
    assert sqlite3.connect(restored).execute("select v from t").fetchone() == ("hello",)
    assert list(path.parent.glob("*.tmp")) == []


def test_in_memory_sqlite_is_rejected(backup_settings):
    with pytest.raises(BackupError):
        services.create_backup()  # test DB is :memory:


def test_postgresql_password_passed_via_env_not_arguments(backup_settings, postgres_db):
    def fake_run(command, **kwargs):
        open(command[command.index("--file") + 1], "wb").write(b"dump")
        assert kwargs["env"]["PGPASSWORD"] == "s3cr3t-pw"
        assert kwargs["timeout"] == 30
        assert not any("s3cr3t-pw" in part for part in command)
        assert command[:4] == ["pg_dump", "--format=custom", "--no-owner", "--no-privileges"]
        return subprocess.CompletedProcess(command, 0, "", "")

    with patch("apps.backups.services.subprocess.run", side_effect=fake_run) as run:
        path = services.create_backup()
    assert run.called and path.name.endswith(".dump")


def test_postgresql_failure_removes_partial_file(backup_settings, postgres_db):
    def fake_run(command, **kwargs):
        open(command[command.index("--file") + 1], "wb").write(b"partial")
        return subprocess.CompletedProcess(command, 1, "", "boom")

    with patch("apps.backups.services.subprocess.run", side_effect=fake_run):
        with pytest.raises(BackupError):
            services.create_backup()
    assert list(services.backup_dir().iterdir()) == []


def test_postgresql_timeout_removes_partial_file(backup_settings, postgres_db):
    def fake_run(command, **kwargs):
        open(command[command.index("--file") + 1], "wb").write(b"partial")
        raise subprocess.TimeoutExpired(command, 30)

    with patch("apps.backups.services.subprocess.run", side_effect=fake_run):
        with pytest.raises(BackupError, match="timed out"):
            services.create_backup()
    assert list(services.backup_dir().iterdir()) == []


def test_unsupported_engine_raises_error(backup_settings, monkeypatch):
    from apps.backups.tests.conftest import FakeConnections

    monkeypatch.setattr(
        "apps.backups.services.connections",
        FakeConnections("mysql", {"ENGINE": "django.db.backends.mysql", "NAME": "x"}),
    )
    with pytest.raises(BackupError, match="Unsupported"):
        services.create_backup()


def test_unknown_alias(backup_settings, sqlite_db):
    with pytest.raises(BackupError):
        services.create_backup("nope")


def test_missing_required_setting_fails_fast(backup_settings, sqlite_db):
    backup_settings.BACKUP_EMAIL_ENABLED = True
    backup_settings.BACKUP_EMAIL_RECIPIENTS = []
    backup_settings.EMAIL_HOST = ""
    with pytest.raises(BackupConfigError) as exc:
        run_backup()
    message = str(exc.value)
    assert "BACKUP_EMAIL_RECIPIENTS" in message and "EMAIL_HOST" in message
    assert list(services.backup_dir().iterdir()) == []  # nothing was created

    backup_settings.BACKUP_EMAIL_ENABLED = False
    backup_settings.BACKUP_GOOGLE_DRIVE_ENABLED = True
    backup_settings.GOOGLE_DRIVE_FOLDER_ID = ""
    with pytest.raises(BackupConfigError, match="GOOGLE_DRIVE_FOLDER_ID"):
        run_backup()


def test_oauth_requires_its_credentials(backup_settings):
    backup_settings.GOOGLE_DRIVE_AUTH_TYPE = "oauth"
    missing = services.missing_settings(False, True)
    assert missing == [
        "GOOGLE_DRIVE_CLIENT_ID", "GOOGLE_DRIVE_CLIENT_SECRET", "GOOGLE_DRIVE_REFRESH_TOKEN",
    ]  # fmt: skip


def test_local_retention_removes_only_old_backup_files(backup_settings, sqlite_db):
    directory = services.backup_dir()
    old_time = time.time() - 30 * 86400
    old_backup = directory / "db-backup-20200101-000000.dump"
    old_gz = directory / "db-backup-20200101-000000.sqlite3.gz"
    old_other = directory / "notes.txt"
    old_prefixless = directory / "other-20200101.dump"
    recent = directory / "db-backup-20991231-000000.dump"
    for f in (old_backup, old_gz, old_other, old_prefixless, recent):
        f.write_bytes(b"x")
    for f in (old_backup, old_gz, old_other, old_prefixless):
        os.utime(f, (old_time, old_time))
    report = run_backup()
    assert report.ok
    remaining = {p.name for p in directory.iterdir()}
    assert "notes.txt" in remaining and "other-20200101.dump" in remaining
    assert recent.name in remaining and report.path.name in remaining
    assert old_backup.name not in remaining and old_gz.name not in remaining


def test_retention_zero_disables_cleanup(backup_settings, sqlite_db):
    backup_settings.BACKUP_RETENTION_DAYS = 0
    old = services.backup_dir() / "db-backup-20200101-000000.dump"
    old.write_bytes(b"x")
    os.utime(old, (1, 1))
    run_backup()
    assert old.exists()


def test_backup_failure_sends_alert_email(backup_settings, postgres_db, mailoutbox):
    backup_settings.BACKUP_EMAIL_ENABLED = True
    with patch("apps.backups.services.subprocess.run", side_effect=OSError("no pg_dump")):
        report = run_backup()
    assert not report.ok and report.path is None
    assert len(mailoutbox) == 1
    body = mailoutbox[0].subject + mailoutbox[0].body
    assert "FAILED" in body and "s3cr3t-pw" not in body


def test_drive_not_imported_when_disabled(backup_settings, sqlite_db):
    sys.modules.pop("apps.backups.destinations.google_drive", None)
    sys.modules.pop("apps.backups.destinations.email", None)
    report = run_backup()
    assert report.ok
    assert "apps.backups.destinations.google_drive" not in sys.modules
    assert "apps.backups.destinations.email" not in sys.modules  # email disabled too

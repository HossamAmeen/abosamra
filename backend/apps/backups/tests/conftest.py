import sqlite3
import sys
from types import SimpleNamespace

import pytest


class FakeConnections:
    """Stands in for django.db.connections so tests control engine/credentials."""

    def __init__(self, vendor, settings_dict):
        self._conn = SimpleNamespace(vendor=vendor, settings_dict=settings_dict)
        self.databases = {"default": {}, "other": {}}

    def __getitem__(self, alias):
        return self._conn


@pytest.fixture
def backup_settings(settings, tmp_path):
    settings.BACKUP_DIR = str(tmp_path / "backups")
    settings.BACKUP_RETENTION_DAYS = 7
    settings.BACKUP_TIMEOUT_SECONDS = 30
    settings.BACKUP_PG_DUMP_PATH = "pg_dump"
    settings.BACKUP_NAME_PREFIX = "db-backup"
    settings.BACKUP_EMAIL_ENABLED = False
    settings.BACKUP_GOOGLE_DRIVE_ENABLED = False
    settings.BACKUP_EMAIL_RECIPIENTS = ["owner@example.com"]
    settings.BACKUP_EMAIL_SUBJECT_PREFIX = "[Test]"
    settings.BACKUP_EMAIL_MAX_ATTACHMENT_MB = 20
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST = "smtp.example.com"
    settings.DEFAULT_FROM_EMAIL = "noreply@example.com"
    settings.GOOGLE_DRIVE_AUTH_TYPE = "service_account"
    settings.GOOGLE_DRIVE_FOLDER_ID = "folder-123"
    settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE = str(tmp_path / "sa.json")
    settings.GOOGLE_DRIVE_RETENTION_DAYS = 30
    return settings


@pytest.fixture
def sqlite_db(tmp_path, monkeypatch):
    path = tmp_path / "live.sqlite3"
    conn = sqlite3.connect(path)
    conn.execute("create table t (id integer primary key, v text)")
    conn.execute("insert into t (v) values ('hello')")
    conn.commit()
    conn.close()
    fake = FakeConnections("sqlite", {"ENGINE": "django.db.backends.sqlite3", "NAME": str(path)})
    monkeypatch.setattr("apps.backups.services.connections", fake)
    return path


@pytest.fixture
def postgres_db(monkeypatch):
    fake = FakeConnections(
        "postgresql",
        {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "abosamra",
            "USER": "abo",
            "PASSWORD": "s3cr3t-pw",
            "HOST": "db",
            "PORT": "5432",
        },
    )
    monkeypatch.setattr("apps.backups.services.connections", fake)
    return fake


@pytest.fixture
def fake_drive(monkeypatch):
    """Replace the Drive client; the google libraries are never needed."""
    from unittest.mock import MagicMock

    sys.modules.pop("apps.backups.destinations.google_drive", None)
    from apps.backups.destinations import google_drive

    service = MagicMock()
    request = service.files.return_value.create.return_value
    request.next_chunk.return_value = (None, {"id": "file-1", "webViewLink": "https://drive/x"})
    service.files.return_value.list.return_value.execute.return_value = {"files": []}
    monkeypatch.setattr(google_drive, "_build_service", lambda: service)
    monkeypatch.setattr(google_drive, "_media", lambda path: "media")
    monkeypatch.setattr(google_drive.time, "sleep", lambda s: None)
    return service

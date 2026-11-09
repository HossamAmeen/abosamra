"""Database backup orchestration. The command (and any task) only calls `run_backup`."""

import gzip
import logging
import os
import shutil
import socket
import sqlite3
import subprocess
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import connections
from django.utils import timezone

logger = logging.getLogger(__name__)

BACKUP_SUFFIXES = (".dump", ".sqlite3.gz")


class BackupError(Exception):
    """Backup creation failed (message is safe to log / email: no secrets)."""


class BackupConfigError(BackupError):
    """An enabled destination is missing required settings."""


@dataclass
class BackupReport:
    path: Path | None = None
    size: int = 0
    engine: str = ""
    created_at: object = None
    drive_link: str = ""
    errors: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.path is not None and not self.errors


# -- configuration -----------------------------------------------------------------
def missing_settings(use_email: bool, use_drive: bool) -> list[str]:
    missing = []
    if use_email:
        for name in ("BACKUP_EMAIL_RECIPIENTS", "EMAIL_HOST", "DEFAULT_FROM_EMAIL"):
            if not getattr(settings, name, None):
                missing.append(name)
    if use_drive:
        if not settings.GOOGLE_DRIVE_FOLDER_ID:
            missing.append("GOOGLE_DRIVE_FOLDER_ID")
        auth = settings.GOOGLE_DRIVE_AUTH_TYPE
        if auth == "service_account":
            required = ["GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE"]
        elif auth == "oauth":
            required = [
                "GOOGLE_DRIVE_CLIENT_ID",
                "GOOGLE_DRIVE_CLIENT_SECRET",
                "GOOGLE_DRIVE_REFRESH_TOKEN",
            ]
        else:
            raise BackupConfigError("GOOGLE_DRIVE_AUTH_TYPE must be 'service_account' or 'oauth'")
        missing += [name for name in required if not getattr(settings, name, "")]
    return missing


def validate_settings(use_email: bool, use_drive: bool) -> None:
    missing = missing_settings(use_email, use_drive)
    if missing:
        raise BackupConfigError("Missing required setting(s): " + ", ".join(missing))


def backup_dir() -> Path:
    path = Path(settings.BACKUP_DIR)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


# -- creation ------------------------------------------------------------------------
def _target(suffix: str) -> Path:
    stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    return backup_dir() / f"{settings.BACKUP_NAME_PREFIX}-{stamp}{suffix}"


def _backup_sqlite(db: dict) -> Path:
    name = str(db["NAME"])
    if name in ("", ":memory:") or name.startswith("file:"):
        raise BackupError("Cannot back up an in-memory SQLite database")
    target = _target(".sqlite3.gz")
    snapshot = target.with_suffix(".tmp")
    try:
        source = sqlite3.connect(name)
        copy = sqlite3.connect(str(snapshot))
        try:
            source.backup(copy)  # consistent even while the app is writing
        finally:
            copy.close()
            source.close()
        with open(snapshot, "rb") as raw, gzip.open(target, "wb") as packed:
            shutil.copyfileobj(raw, packed)
    except (sqlite3.Error, OSError) as exc:
        target.unlink(missing_ok=True)
        raise BackupError(f"SQLite backup failed: {exc.__class__.__name__}") from exc
    finally:
        snapshot.unlink(missing_ok=True)
    return target


def _backup_postgresql(db: dict) -> Path:
    target = _target(".dump")
    command = [
        settings.BACKUP_PG_DUMP_PATH,
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file",
        str(target),
        "--dbname",
        str(db["NAME"]),
    ]
    for flag, key in (("--host", "HOST"), ("--port", "PORT"), ("--username", "USER")):
        if db.get(key):
            command += [flag, str(db[key])]
    env = {**os.environ}
    if db.get("PASSWORD"):
        env["PGPASSWORD"] = str(db["PASSWORD"])  # never on the command line
    try:
        result = subprocess.run(  # noqa: S603
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=settings.BACKUP_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        target.unlink(missing_ok=True)
        raise BackupError("pg_dump timed out") from exc
    except OSError as exc:
        target.unlink(missing_ok=True)
        raise BackupError(f"pg_dump could not be started ({exc.__class__.__name__})") from exc
    if result.returncode != 0:
        target.unlink(missing_ok=True)
        logger.error("pg_dump failed: %s", (result.stderr or "")[-500:])
        raise BackupError(f"pg_dump failed with exit code {result.returncode}")
    return target


def create_backup(alias: str = "default") -> Path:
    if alias not in connections.databases:
        raise BackupError(f"Unknown database alias: {alias}")
    db = connections[alias].settings_dict
    vendor = connections[alias].vendor
    if vendor == "sqlite":
        path = _backup_sqlite(db)
    elif vendor == "postgresql":
        path = _backup_postgresql(db)
    else:
        raise BackupError(f"Unsupported database engine: {db['ENGINE']}")
    os.chmod(path, 0o600)
    return path


def engine_label(alias: str = "default") -> str:
    return connections[alias].settings_dict["ENGINE"]


# -- retention ---------------------------------------------------------------------------
def cleanup_local(keep: Path | None = None) -> list[Path]:
    """Delete backup files (matching prefix + known suffix) older than the retention."""
    days = settings.BACKUP_RETENTION_DAYS
    if days <= 0:
        return []
    cutoff = (timezone.now() - timedelta(days=days)).timestamp()
    removed = []
    for path in backup_dir().iterdir():
        if (
            path.is_file()
            and path != keep
            and path.name.startswith(settings.BACKUP_NAME_PREFIX)
            and path.name.endswith(BACKUP_SUFFIXES)
            and path.stat().st_mtime < cutoff
        ):
            path.unlink()
            removed.append(path)
            logger.info("Removed old local backup %s", path.name)
    return removed


# -- orchestration --------------------------------------------------------------------------
def run_backup(alias="default", *, use_email=True, use_drive=True) -> BackupReport:
    """Flags can only switch a destination off for this run, never on."""
    email_on = bool(settings.BACKUP_EMAIL_ENABLED and use_email)
    drive_on = bool(settings.BACKUP_GOOGLE_DRIVE_ENABLED and use_drive)
    validate_settings(email_on, drive_on)  # fail fast, before any work

    report = BackupReport(engine=engine_label(alias), created_at=timezone.now())
    host = socket.gethostname()

    try:
        report.path = create_backup(alias)
    except BackupError as exc:
        logger.error("Backup creation failed: %s", exc)
        report.errors.append(f"backup: {exc}")
        if email_on:
            from .destinations import email as email_destination

            email_destination.send_failure_alert(str(exc), engine=report.engine, host=host)
        return report
    report.size = report.path.stat().st_size
    report.steps.append(f"created {report.path.name} ({report.size} bytes)")
    logger.info("Backup created: %s", report.path.name)

    drive_error = ""
    if drive_on:
        from .destinations import google_drive

        try:
            result = google_drive.upload(report.path)
            report.drive_link = result.get("link", "")
            report.steps.append("uploaded to Google Drive")
        except Exception as exc:  # destinations are independent
            drive_error = str(exc)
            logger.error("Drive upload failed: %s", exc)
            report.errors.append(f"google_drive: {exc}")

    if email_on:
        from .destinations import email as email_destination

        try:
            email_destination.send_backup_email(
                report, host=host, drive_enabled=drive_on, drive_error=drive_error
            )
            report.steps.append("emailed")
        except Exception as exc:
            logger.error("Backup email failed: %s", exc)
            report.errors.append(f"email: {exc}")

    try:
        cleanup_local(keep=report.path)
    except OSError as exc:
        logger.error("Local retention cleanup failed: %s", exc)
        report.errors.append(f"retention: {exc.__class__.__name__}")

    if drive_on and not drive_error and settings.GOOGLE_DRIVE_RETENTION_DAYS > 0:
        from .destinations import google_drive

        try:
            google_drive.cleanup_remote()
        except Exception as exc:
            logger.error("Drive retention cleanup failed: %s", exc)
            report.errors.append(f"google_drive_retention: {exc}")
    return report

"""Email destination: notification (+ attachment when small enough)."""

import logging

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def _subject(text: str) -> str:
    return f"{settings.BACKUP_EMAIL_SUBJECT_PREFIX} {text}".strip()


def send_backup_email(report, *, host: str, drive_enabled: bool, drive_error: str = "") -> None:
    path = report.path
    limit = settings.BACKUP_EMAIL_MAX_ATTACHMENT_MB * 1024 * 1024
    attach = report.size <= limit
    lines = [
        f"Server: {host}",
        f"Database engine: {report.engine}",
        f"File: {path.name}",
        f"Size: {report.size / 1024 / 1024:.2f} MB",
        f"Created: {report.created_at.isoformat()}",
    ]
    if report.drive_link:
        lines.append(f"Google Drive: {report.drive_link}")
    elif drive_enabled and drive_error:
        lines.append("Google Drive upload FAILED (see server logs).")
    if not attach:
        lines.append(
            f"The file is larger than {settings.BACKUP_EMAIL_MAX_ATTACHMENT_MB} MB so it is not "
            f"attached. It is stored on the server in {settings.BACKUP_DIR}."
        )
    subject = _subject("Database backup" + (" (Drive upload failed)" if drive_error else ""))
    message = EmailMessage(
        subject,
        "\n".join(lines),
        settings.DEFAULT_FROM_EMAIL,
        list(settings.BACKUP_EMAIL_RECIPIENTS),
    )
    if attach:
        message.attach_file(str(path))
    message.send(fail_silently=False)


def send_failure_alert(reason: str, *, engine: str, host: str) -> None:
    """Never raises: an alert must not mask the original failure."""
    try:
        EmailMessage(
            _subject("Database backup FAILED"),
            f"Server: {host}\nDatabase engine: {engine}\nReason: {reason}",
            settings.DEFAULT_FROM_EMAIL,
            list(settings.BACKUP_EMAIL_RECIPIENTS),
        ).send(fail_silently=False)
    except Exception:
        logger.exception("Could not send the backup failure alert")

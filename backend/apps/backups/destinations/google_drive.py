"""Google Drive destination. Google libraries are imported lazily, only when used."""

import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
MAX_ATTEMPTS = 3
TOKEN_URI = "https://oauth2.googleapis.com/token"


class DriveError(Exception):
    pass


def _build_service():
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    if settings.GOOGLE_DRIVE_AUTH_TYPE == "oauth":
        creds = Credentials(
            None,
            refresh_token=settings.GOOGLE_DRIVE_REFRESH_TOKEN,
            token_uri=TOKEN_URI,
            client_id=settings.GOOGLE_DRIVE_CLIENT_ID,
            client_secret=settings.GOOGLE_DRIVE_CLIENT_SECRET,
            scopes=SCOPES,
        )
    else:
        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _media(path: Path):
    from googleapiclient.http import MediaFileUpload

    return MediaFileUpload(str(path), mimetype="application/octet-stream", resumable=True)


def _status(exc) -> int | None:
    resp = getattr(exc, "resp", None)
    status = getattr(resp, "status", None)
    return int(status) if status is not None else None


def _retryable(exc) -> bool:
    status = _status(exc)
    if status is not None:
        return status == 429 or status >= 500
    return isinstance(exc, OSError | TimeoutError)  # network problems


def _with_retries(action):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return action()
        except Exception as exc:
            if not _retryable(exc) or attempt == MAX_ATTEMPTS:
                raise DriveError(f"Drive request failed ({exc.__class__.__name__})") from exc
            delay = 2**attempt
            logger.warning("Drive request failed (attempt %s), retrying in %ss", attempt, delay)
            time.sleep(delay)


def upload(path: Path) -> dict:
    """Resumable upload into GOOGLE_DRIVE_FOLDER_ID; returns {id, link}."""
    service = _build_service()
    body = {"name": path.name, "parents": [settings.GOOGLE_DRIVE_FOLDER_ID]}

    def action():
        request = service.files().create(
            body=body, media_body=_media(path), fields="id, webViewLink", supportsAllDrives=True
        )
        response = None
        while response is None:
            _, response = request.next_chunk()
        return response

    response = _with_retries(action)
    logger.info("Uploaded %s to Google Drive", path.name)
    return {"id": response.get("id"), "link": response.get("webViewLink", "")}


def cleanup_remote() -> list[str]:
    """Delete only prefixed files older than GOOGLE_DRIVE_RETENTION_DAYS in the folder."""
    days = settings.GOOGLE_DRIVE_RETENTION_DAYS
    if days <= 0:
        return []
    prefix = settings.BACKUP_NAME_PREFIX
    cutoff = datetime.now(UTC) - timedelta(days=days)
    service = _build_service()
    folder = settings.GOOGLE_DRIVE_FOLDER_ID
    deleted, page_token = [], None
    while True:
        listing = _with_retries(
            lambda token=page_token: service.files()
            .list(
                q=f"'{folder}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, createdTime)",
                pageSize=200,
                pageToken=token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        for item in listing.get("files", []):
            created = datetime.fromisoformat(item["createdTime"].replace("Z", "+00:00"))
            if item["name"].startswith(prefix) and created < cutoff:
                _with_retries(
                    lambda file_id=item["id"]: service.files()
                    .delete(fileId=file_id, supportsAllDrives=True)
                    .execute()
                )
                deleted.append(item["name"])
                logger.info("Removed old Drive backup %s", item["name"])
        next_token = listing.get("nextPageToken")
        if not isinstance(next_token, str) or not next_token or next_token == page_token:
            return deleted
        page_token = next_token

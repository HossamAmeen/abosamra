# Abo Samra backend

Django REST Framework API (Python 3.12). Django root is this directory.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
make install-dev
cp .env.example .env      # then edit secrets
make migrate
make run
make test                 # pytest
make coverage
```

Docker (api + postgres): `make docker-local`, then open `http://localhost:8000/api/docs/`.
Health: `curl -H "X-Health-Check-Token: $HEALTH_CHECK_PASSWORD" localhost:8000/api/health/`.

Settings: `config.settings.{development,production,test}`; all config via `.env`.

## Seed data

`python manage.py seed_abo_samra` (idempotent; staff user from `ADMIN_PHONE` / `ADMIN_PASSWORD` / `ADMIN_NAME`).

## Database backup

`python manage.py backup_db` writes a local backup to `BACKUP_DIR` (`.dump` for PostgreSQL via `pg_dump`,
`.sqlite3.gz` for SQLite), then optionally uploads to Google Drive and/or emails it. Everything is
configured in `.env` (see `.env.example`): `BACKUP_EMAIL_ENABLED`, `BACKUP_GOOGLE_DRIVE_ENABLED`,
retention (`BACKUP_RETENTION_DAYS`, `GOOGLE_DRIVE_RETENTION_DAYS`). Flags only turn a destination off
for one run: `--no-email`, `--no-drive`, `--local-only`, `--database ALIAS`. Exit code is non-zero if the
backup or any enabled destination failed. Schedule with a systemd timer (`make backup`) - never expose
`BACKUP_DIR` over HTTP; backups contain the whole database.

Restore:

```bash
# SQLite
gunzip -c <file>.sqlite3.gz > db.sqlite3
# PostgreSQL
pg_restore --clean --no-owner -d <database> <file>.dump
```

Google Drive: a service account has no quota, so the folder must be in a Shared Drive that the service
account is a member of (or use `GOOGLE_DRIVE_AUTH_TYPE=oauth`). Keep the JSON key outside the repo.

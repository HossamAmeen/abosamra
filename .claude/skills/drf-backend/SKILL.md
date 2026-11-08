---
name: drf-backend
description: Use when creating, refactoring or extending a Django REST Framework backend: project layout, settings, JWT, throttling, health API, tests, Docker, deployment and DB backups.
---

# Django REST Framework Engineering Skill

Defines the standard architecture, workflow, testing, Docker, deployment and engineering rules for DRF backends. It is **domain-agnostic** (SaaS, e-commerce, delivery, healthcare, ERP, CRM, booking, fintech, internal APIs, microservices).

**Business requirements decide WHAT the system does. This skill decides HOW the backend is structured, configured, implemented, tested, documented, containerized, deployed and maintained.**

## Precedence with a project spec

When a project prompt/spec is supplied alongside this skill:
- **Conventions** (layout, settings split, env vars, Docker, CI, tests, code style) → this skill wins.
- **API contract and business rules** (paths, field names, status codes, error/response shapes, auth flow, token lifetimes, pricing, state machines) → the project spec wins.
- In particular, if the spec defines its own error/response format (e.g. `{"detail", "code"}` and DRF-default field errors), implement the centralized exception handler to emit **that** format instead of the `success/message/data` envelope below. Apply the same to health and 429 responses.
- If the spec pins a different Python version or app names, follow the spec. List every conflict you resolved in the final summary.

## Modes

- **CREATE** — new project.
- **REFACTOR** — improve an existing Django/DRF project.
- **UPDATE** — add or modify functionality in an existing project.

## Engineering principles

The agent MUST:
- Read and understand the project before changing it.
- Separate business domains into Django apps; keep shared infrastructure in `common/`.
- Keep business logic in the backend. The backend is the source of truth for business rules, validation, authorization, state transitions, data integrity, security, calculations and lifecycle rules. Frontends (web, PWA, Flutter, mobile) must not duplicate them.
- Use environment variables for config and secrets. Never hardcode secrets, domains, ports, filesystem paths or service names.
- Use automated tests for business behavior; use migrations for every schema change.
- Preserve behavior and backward compatibility when refactoring; prefer incremental, testable changes; avoid rewrites.
- Keep API contracts consistent. Treat deployment configuration as code.
- Validate before declaring work complete.

## Technology stack

Required: Python 3.13+, Django, DRF, django-environ, dj-database-url, djangorestframework-simplejwt, drf-spectacular, django-jazzmin, pytest, pytest-django, pytest-cov, Docker, Docker Compose.

Database: SQLite for local development; PostgreSQL for staging and production.

Optional (controlled by env): Redis, Celery, Celery Beat, Nginx, systemd.

## Standard project structure

```
backend/
├── manage.py
├── config/
│   ├── __init__.py
│   ├── celery.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── __init__.py
│   ├── users/
│   │   ├── __init__.py  admin.py  apps.py  models.py  managers.py
│   │   ├── serializers.py  views.py  urls.py  permissions.py
│   │   ├── services.py  selectors.py  tasks.py
│   │   ├── tests/
│   │   │   ├── __init__.py  conftest.py
│   │   │   ├── test_models.py  test_serializers.py  test_views.py
│   │   │   ├── test_services.py  test_tasks.py
│   │   └── migrations/
│   └── <domain_apps>/
├── common/
│   ├── __init__.py  models.py  managers.py  exceptions.py
│   ├── exception_handler.py  responses.py  pagination.py
│   ├── permissions.py  throttling.py
├── tests/
│   ├── __init__.py
│   └── conftest.py
├── requirements/
│   ├── base.txt  development.txt  production.txt
├── docker/
│   ├── local/       (Dockerfile, docker-compose.yml)
│   ├── staging/     (Dockerfile, docker-compose.yml)
│   └── production/  (Dockerfile, docker-compose.yml)
├── deploy/
│   ├── nginx/      generate.sh, templates/nginx.conf.template
│   ├── systemd/    templates/backend.service.template
│   └── scripts/    deploy.sh migrate.sh collectstatic.sh restart.sh healthcheck.sh
├── scripts/
│   ├── entrypoint.sh
│   └── wait_for_db.sh
├── .env  .env.example  .gitignore
├── Makefile
├── pytest.ini
└── README.md
```

Adapt for existing projects; do not force a large refactor just to match this layout if the existing architecture is valid.

## CREATE mode

Order: Requirements → Project structure → Settings → Environment config → Database → DRF → JWT → Common infrastructure → OpenAPI → Jazzmin → Health API → Testing → Docker → Celery/Redis (if enabled) → Deployment structure → Domain apps → Business features → Validation.

Establish the foundation before business features.

## REFACTOR mode

Do NOT rewrite immediately. First inspect: structure, settings, requirements, models, managers, views/viewsets, serializers, URLs, permissions, authentication, services, selectors, tasks, tests, migrations, env config, Docker/Compose, Nginx, systemd, deploy scripts, API docs, Celery config.

Then identify: current architecture, problems, technical debt, security risks, testing gaps, deployment problems, performance problems, potential breaking changes, and a recommended order.

Refactor incrementally in this order:
1. Environment configuration
2. Settings separation
3. Common infrastructure
4. Authentication
5. Exception handling
6. Response standardization
7. Base model
8. Soft delete / managers
9. Domain separation
10. Services / selectors
11. Testing
12. OpenAPI
13. Docker
14. Deployment
15. Performance

Never perform a large rewrite without a clear reason.

## UPDATE mode

Read → Understand → Identify affected domain → Inspect existing implementation → Inspect tests → Implement → Add/update tests → Update OpenAPI → Run validation. Do not modify unrelated functionality.

## Settings

Never one settings file. Use `config/settings/{base,development,production}.py`.
- `base.py`: installed apps, middleware, DRF, authentication, JWT, OpenAPI, Jazzmin, i18n, static/media, shared security, Celery.
- `development.py`: local config. `production.py`: production config.

## Environment variables

Use `.env` locally. Commit only `.env.example`; never commit `.env`.

```dotenv
# Django
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=30
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Health API
HEALTH_CHECK_PASSWORD=change-me

# Celery
CELERY_ENABLED=False
CELERY_BEAT_ENABLED=False
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_ALWAYS_EAGER=False
CELERY_TASK_EAGER_PROPAGATES=False
CELERY_WORKER_CONCURRENCY=2

# API rate limiting
RATELIMIT_ANON=60/minute
RATELIMIT_USER=300/minute
RATELIMIT_AUTH=10/minute
RATELIMIT_SENSITIVE=30/minute
RATELIMIT_HEALTH=120/minute
RATELIMIT_CACHE_URL=redis://localhost:6379/2

# Deployment
DOMAIN=example.com
BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_PATH=/opt/myapp/backend
FRONTEND_PATH=/opt/myapp/frontend
MEDIA_PATH=/opt/myapp/backend/media
STATIC_PATH=/opt/myapp/backend/static
SYSTEMD_SERVICE_NAME=myapp-backend
```

(Backup variables are listed in the Database Backup section.)

Never hardcode: passwords, secret keys, DB credentials, API keys, JWT secrets, domains, ports, filesystem paths, systemd service names.

## Database

```python
import dj_database_url

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///db.sqlite3",
        conn_max_age=600,
    )
}
```

All schema changes MUST use migrations.

## Common package

Use `common/` (not `utils/`) for shared architectural infrastructure. Only code shared across multiple apps belongs there; domain code stays in its app. Do not turn `utils/` into a dumping ground.

### Base model — `common/models.py`

```python
from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
```

### Soft delete

Soft delete sets `deleted_at = timezone.now()` instead of physically deleting. Provide `soft_delete()` and `restore()` where appropriate.

### Managers — `common/managers.py`

```python
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class DeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=False)

class AllManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

class Example(BaseModel):
    objects = ActiveManager()
    deleted_objects = DeletedManager()
    all_objects = AllManager()
```

The default manager normally returns only active records.

## Django apps

Separate business domains into apps (e.g. `users/`, `orders/`, `products/`, `payments/`, `notifications/`); the actual apps depend on requirements. Never one giant app.

## DRF API architecture

Every API has the appropriate serializer, view/viewset, URL, permission, validation and tests. Use the simplest suitable DRF abstraction.

Business logic layers: `models.py`, `services.py` (workflows / writes), `selectors.py` (complex reads / queries).

## Authentication & authorization

- `djangorestframework-simplejwt` with access + refresh tokens. Typical endpoints: `POST /api/auth/token/`, `POST /api/auth/token/refresh/` (project spec may define its own auth endpoints).
- JWT settings from env where appropriate.
- Use DRF permissions: `IsAuthenticated`, `IsAdminUser`, custom role permissions, object-level permissions. Never rely on frontend permissions for security.

## Standard API responses

Default envelope (used unless the project spec defines another contract — see Precedence):

```json
{ "success": true, "message": "Operation completed successfully.", "data": {} }
```
```json
{ "success": false, "message": "Validation failed.", "errors": { "field": ["This field is required."] } }
```

In an existing project, do not change an established response contract unnecessarily.

## Centralized exception handling — `common/exception_handler.py`

Handle: validation, authentication, permission, not found, throttling, custom application exceptions, unexpected exceptions. All errors follow the project's standard structure. Never format exceptions inside individual views.

## OpenAPI — drf-spectacular

Expose `/api/schema/`, `/api/docs/`, `/api/redoc/` where appropriate. Document every public API: request body, response, auth, query and path params, important validation rules, and `429` for rate-limited endpoints.

## Django Jazzmin

```python
INSTALLED_APPS = [
    "jazzmin",  # before django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
]

JAZZMIN_SETTINGS = {
    "site_title": "Django Admin",
    "site_header": "Django Administration",
    "site_brand": "Backend",
    "welcome_sign": "Welcome to the administration panel",
    "copyright": "Backend",
    "show_sidebar": True,
    "navigation_expanded": True,
}
```

Jazzmin config must not be coupled to a business domain (branding text may come from settings/env). Admin stays protected by Django auth + staff/superuser permissions.

## Health API

Every new project provides `GET /api/health/`, protected by `HEALTH_CHECK_PASSWORD` from `.env` (never hardcoded).
- Accept `?password=<HEALTH_CHECK_PASSWORD>`; in production prefer the `X-Health-Check-Token` header (query strings land in access logs).
- Success: `{ "success": true, "message": "Service is healthy.", "data": { "status": "healthy" } }`
- Invalid password: `{ "success": false, "message": "Invalid health check password.", "errors": {} }`
- Never expose env vars, passwords, DB credentials, secret keys, stack traces, filesystem paths or internal exceptions.
- Basic health only checks Django is running — no dependency on optional services.
- Optional `GET /api/health/ready/` may check DB, Redis, Celery, required external services; when `CELERY_ENABLED=False` it must not require Celery.

Required tests: `test_health_endpoint_returns_success_with_valid_password`, `test_health_endpoint_rejects_invalid_password`, `test_health_endpoint_requires_password`, `test_health_endpoint_does_not_expose_secret`. Readiness tests cover dependency failures. Tests use test values, never production secrets.

## Celery (optional)

The same code must run with `CELERY_ENABLED=False` and `True` without changes.
- Disabled: Django starts normally, Redis not required, no workers, no Beat.
- Enabled: broker must be available, workers deployed; Beat only when `CELERY_BEAT_ENABLED=True`.

`config/celery.py`:

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

`config/__init__.py`:

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

(If Celery is not installed in a project that never enables it, guard this import or omit the module.)

Rules:
- Tasks live in the app that owns the feature (e.g. `apps/notifications/tasks.py`).
- Tasks are thin wrappers: Task → Service → Business logic → DB. No large workflows inside tasks.
- Dispatch after commit: `transaction.on_commit(lambda: task.delay(obj.id))`.
- External-system tasks consider retries, backoff, max retries, failure handling, idempotency. Never blindly retry non-idempotent operations.
- Docker: provide `redis` + `celery-worker` only when enabled; `celery-beat` only when Beat is enabled.

## API rate limiting

All public APIs MUST be rate limited, at the backend (never the frontend's job). Enable globally so new endpoints are protected by default:

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("RATELIMIT_ANON", default="60/minute"),
        "user": env("RATELIMIT_USER", default="300/minute"),
        "auth": env("RATELIMIT_AUTH", default="10/minute"),
        "sensitive": env("RATELIMIT_SENSITIVE", default="30/minute"),
        "health": env("RATELIMIT_HEALTH", default="120/minute"),
    },
}
```

`common/throttling.py`:

```python
from rest_framework.throttling import UserRateThrottle

class AuthRateThrottle(UserRateThrottle):
    scope = "auth"

class SensitiveRateThrottle(UserRateThrottle):
    scope = "sensitive"
```

Rules:
- Anonymous requests throttled by client IP; authenticated by user (not just IP, to avoid NAT sharing).
- Auth endpoints (login/token/refresh) MUST be stricter than normal APIs. Sensitive operations (password reset, OTP, email/SMS verification, payments, account recovery, expensive search, file processing, external API proxies) get stricter limits too.
- Rates come from env; never hardcode production limits.
- Multi-instance staging/production MUST use a shared cache (Redis), never local in-memory:
  ```python
  CACHES = {
      "default": {
          "BACKEND": "django.core.cache.backends.redis.RedisCache",
          "LOCATION": env("RATELIMIT_CACHE_URL", default="redis://localhost:6379/2"),
      }
  }
  ```
  Suggested Redis DBs: 0 Celery broker, 1 Celery results, 2 throttling/cache. Rate limiting must not depend on Celery.
- Exceeding the limit → HTTP 429 in the project's standard error structure (default `{ "success": false, "message": "Request rate limit exceeded.", "errors": {} }`), retry headers where supported, no internals.
- Behind Nginx/load balancers, configure trusted proxies explicitly; never blindly trust `X-Forwarded-For`.
- Health endpoint gets its own scope so deploy checks are not blocked; do not fully disable throttling on public health endpoints without a documented reason.
- Staging/production Compose must provide Redis (or configure external Redis) when required.
- Never disable throttling on an endpoint without a documented reason.

Required tests (isolated test cache, never production Redis): `test_api_allows_requests_within_rate_limit`, `test_api_rejects_requests_after_rate_limit`, `test_anonymous_user_uses_anonymous_throttle`, `test_authenticated_user_uses_user_throttle`, `test_auth_endpoint_uses_stricter_throttle`, and for sensitive endpoints `test_sensitive_endpoint_has_stricter_rate_limit`. `make test` must run them; optionally add `test-rate-limit: pytest -k "throttle or rate_limit"`.

## Testing

pytest + pytest-django + pytest-cov. Every business feature has tests covering:
- **Models**: creation, modification, soft delete, restore, managers, constraints, methods.
- **Serializers**: valid/invalid input, required fields, validation, representation.
- **APIs**: authentication, authorization, success, validation errors, not found, permissions, pagination, filtering.
- **Services**: happy paths, business rules, failure cases, edge cases, transactions.
- **Celery**: execution, arguments, success, failure, retries, idempotency where applicable.

Fixtures: global in `tests/conftest.py`, app-specific in `apps/<app>/tests/conftest.py` (users, API clients, auth, domain objects, roles, permissions, common data). No duplicated setup.

Coverage: `pytest --cov=. --cov-report=term-missing`, meaningful tests only, initial minimum 80% unless the project says otherwise.

`pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests.py test_*.py *_tests.py
addopts = --strict-markers
```

## Migrations

`python manage.py makemigrations` / `migrate`; validate with `makemigrations --check`. Never destructively modify migration history in an established project without explicit approval.

## Query performance & pagination

Avoid N+1 with `select_related()` / `prefetch_related()` where appropriate; don't optimize prematurely. Paginate collection APIs; never expose unbounded querysets publicly.

## Docker

Separate by environment: `docker/local/`, `docker/staging/`, `docker/production/` (each with Dockerfile + docker-compose.yml).
- **Local**: optimize DX; may include backend, database, redis, celery-worker, celery-beat. SQLite is fine when PostgreSQL isn't required.
- **Staging**: as close to production as practical (backend, postgres, redis, celery-worker, celery-beat, nginx — only what's needed); isolated from production.
- **Production**: backend, postgres, redis, celery-worker, celery-beat, nginx as needed. Managed infrastructure may replace Docker services.
- Optional Compose healthcheck against `/api/health/` (interval 30s, timeout 10s, retries 3) using a secure way to pass the token; don't expose credentials.

## Makefile

Every new project has one:

```makefile
install:            pip install -r requirements/base.txt
install-dev:        pip install -r requirements/development.txt
run:                python manage.py runserver
migrate:            python manage.py migrate
makemigrations:     python manage.py makemigrations
test:               pytest
coverage:           pytest --cov=. --cov-report=term-missing
check:              python manage.py check
lint:               ruff check .
format:             ruff format .
shell:              python manage.py shell
collectstatic:      python manage.py collectstatic --noinput
celery-worker:      celery -A config worker --loglevel=INFO
celery-beat:        celery -A config beat --loglevel=INFO
docker-local:       docker compose -f docker/local/docker-compose.yml up --build
docker-staging:     docker compose -f docker/staging/docker-compose.yml up --build -d
docker-production:  docker compose -f docker/production/docker-compose.yml up --build -d
deploy-staging:     bash deploy/scripts/deploy.sh staging
deploy-production:  bash deploy/scripts/deploy.sh production
backup:             python manage.py backup_db
backup-local:       python manage.py backup_db --local-only
```

(Write as proper make targets with tab-indented recipes.) Project-specific commands may be added.

## Deployment

All deployment config lives in `deploy/` and reads from `.env` (at minimum `DOMAIN`, `BACKEND_PORT`, `FRONTEND_PORT`, `BACKEND_PATH`, `FRONTEND_PATH`, `MEDIA_PATH`, `STATIC_PATH`, `SYSTEMD_SERVICE_NAME`, `HEALTH_CHECK_PASSWORD`). Never hardcode these in scripts.

### Nginx

Template `deploy/nginx/templates/nginx.conf.template` + generator `deploy/nginx/generate.sh` reading env vars:

```nginx
server {
    listen 80;
    server_name ${DOMAIN};

    location /api/    { proxy_pass http://127.0.0.1:${BACKEND_PORT}; }
    location /media/  { alias ${MEDIA_PATH}/; }
    location /static/ { alias ${STATIC_PATH}/; }
    location / {
        root ${FRONTEND_PATH};
        try_files $uri $uri/ /index.html;
    }
}
```

Adapt to the real project; never hardcode domain, port or paths.

### systemd

`deploy/systemd/templates/backend.service.template` (values from `.env`: `SYSTEMD_SERVICE_NAME`, `BACKEND_PATH`, `BACKEND_PORT`):

```ini
[Unit]
Description=${SYSTEMD_SERVICE_NAME}
After=network.target

[Service]
WorkingDirectory=${BACKEND_PATH}
ExecStart=${BACKEND_PATH}/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:${BACKEND_PORT}
Restart=always

[Install]
WantedBy=multi-user.target
```

Gunicorn, Uvicorn or another suitable server.

### Scripts

Required: `deploy/scripts/{deploy,migrate,collectstatic,restart,healthcheck}.sh`, using `set -euo pipefail` where appropriate; never print secrets.

Flow: Load env → Validate required vars → Build/pull → Install deps → Migrate → Collectstatic → Generate Nginx config → Generate/update systemd → Restart backend → Start required Celery services → Health check.

The health-check script reads `DOMAIN`, `HEALTH_CHECK_PASSWORD`, `BACKEND_PORT`; deployment fails if the backend doesn't become healthy; never print the password.

### Environment separation

Keep local / staging / production clearly separated (`docker/*`, `config/settings/*`). Never deploy staging config to production; never use production credentials locally.

## Security

Never hardcode passwords, secret keys, DB credentials, API keys, JWT secrets, health secrets, domains, production paths or service names. Don't expose `.env` or log sensitive env vars. Keep Django Admin protected. Never expose health credentials.

## Backward compatibility

In existing projects preserve API contracts, data, auth behavior and business behavior. Avoid unnecessary field renames, endpoint removals and destructive migrations. Clearly identify breaking changes.

## API contract flow

For significant features: Requirement → Domain analysis → Data model → API contract → Serializer → Service → View → Permission → Tests → OpenAPI. Define the contract before dependent frontend clients are built.

## Database backup

Every project MUST provide `python manage.py backup_db`, configured entirely through `.env`, optionally emailed and/or uploaded to Google Drive, safe to schedule. Each destination has its own flag; business code never changes when one is toggled.

### Command flags

Flags can only turn a destination off for one run, never enable a disabled one:
- `--no-email` — skip email even if enabled
- `--no-drive` — skip Drive even if enabled
- `--local-only` — local backup only
- `--database` — DB alias (default `default`)

### Structure

```
apps/backups/
├── __init__.py  apps.py
├── services.py              # create backup, run destinations, cleanup, orchestration
├── destinations/
│   ├── __init__.py
│   ├── email.py             # send by email
│   └── google_drive.py      # upload to Drive
├── tasks.py                 # optional Celery task, thin wrapper
├── management/commands/backup_db.py   # thin: parse flags, call service, report
└── tests/
    ├── __init__.py  conftest.py
    ├── test_services.py  test_email_destination.py
    ├── test_google_drive_destination.py  test_command.py
```

The command and the Celery task MUST NOT contain backup logic.

### Environment

```dotenv
# Database backup
BACKUP_DIR=/opt/myapp/backups
BACKUP_RETENTION_DAYS=7
BACKUP_TIMEOUT_SECONDS=1800
BACKUP_PG_DUMP_PATH=pg_dump
BACKUP_NAME_PREFIX=db-backup

# Destination flags
BACKUP_EMAIL_ENABLED=False
BACKUP_GOOGLE_DRIVE_ENABLED=False

# Backup email
BACKUP_EMAIL_RECIPIENTS=admin@example.com
BACKUP_EMAIL_SUBJECT_PREFIX=[MyApp]
BACKUP_EMAIL_MAX_ATTACHMENT_MB=20

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=change-me
EMAIL_HOST_PASSWORD=change-me
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_TIMEOUT=60
DEFAULT_FROM_EMAIL=noreply@example.com

# Google Drive
GOOGLE_DRIVE_AUTH_TYPE=service_account
GOOGLE_DRIVE_FOLDER_ID=change-me
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=/opt/myapp/secrets/google-drive-sa.json
GOOGLE_DRIVE_CLIENT_ID=
GOOGLE_DRIVE_CLIENT_SECRET=
GOOGLE_DRIVE_REFRESH_TOKEN=
GOOGLE_DRIVE_RETENTION_DAYS=30

# Schedule (Celery Beat or systemd timer)
BACKUP_CRON_HOUR=3
BACKUP_CRON_MINUTE=0
```

Read everything in `config/settings/base.py` with django-environ; flags via `env.bool()`, recipient lists via `env.list()`. Never hardcode recipients, folder IDs, credentials, paths or SMTP values.

### Destination rules

- Both flags False → local backup only.
- Email True → send by email. Drive True → upload to Drive.
- Both True → upload to Drive first, then email including the Drive link when the upload succeeded.
- A disabled destination is never imported, configured or contacted. Google libraries are imported lazily inside `destinations/google_drive.py`.
- Enabled destination with missing settings → fail fast, naming the missing variable (never its value). Email needs `BACKUP_EMAIL_RECIPIENTS`, `EMAIL_HOST`, `DEFAULT_FROM_EMAIL`; Drive needs `GOOGLE_DRIVE_FOLDER_ID` + credentials for `GOOGLE_DRIVE_AUTH_TYPE`.

### Backup creation

- **SQLite**: sqlite3 backup API (consistent while running), gzip → `<PREFIX>-YYYYMMDD-HHMMSS.sqlite3.gz`.
- **PostgreSQL**: `pg_dump --format=custom --no-owner --no-privileges` → `<PREFIX>-YYYYMMDD-HHMMSS.dump`. Password via `PGPASSWORD` env, never in arguments. Apply `BACKUP_TIMEOUT_SECONDS`. Delete the partial file on failure.
- Unsupported engine → clear `BackupError`.
- Read connection details from `connections[alias].settings_dict`, never re-parse `DATABASE_URL`. Timestamps via `timezone.now()`.

### Email destination

Django `EmailMessage` with SMTP settings from `.env`. Body includes server hostname, DB engine, file name, size, created time, Drive link (if uploaded). If the file exceeds `BACKUP_EMAIL_MAX_ATTACHMENT_MB`, don't attach; send the notification and state where the file is stored. Note: Gmail SMTP needs an App Password and rejects attachments over 25 MB.

### Google Drive destination

Dependencies (add to `requirements/base.txt` only when used): `google-api-python-client`, `google-auth`, `google-auth-oauthlib`.

Auth modes (`GOOGLE_DRIVE_AUTH_TYPE`):
- `service_account` — uses `GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE`. Service accounts have no personal quota: the folder MUST be in a Shared Drive and the service account a member of it. A normal "My Drive" folder fails with a quota error.
- `oauth` — uses `GOOGLE_DRIVE_CLIENT_ID`, `GOOGLE_DRIVE_CLIENT_SECRET`, `GOOGLE_DRIVE_REFRESH_TOKEN` (generated once outside the app). For personal accounts without a Shared Drive.

Scope: `https://www.googleapis.com/auth/drive.file`.

Upload: resumable `MediaFileUpload(resumable=True)`, `parents=[GOOGLE_DRIVE_FOLDER_ID]`, always `supportsAllDrives=True`, return file ID + `webViewLink`. Retry transient errors (429, 5xx, network) with exponential backoff, max 3 attempts; never retry 4xx auth/permission errors.

Remote retention: when `GOOGLE_DRIVE_RETENTION_DAYS > 0`, delete only files starting with `BACKUP_NAME_PREFIX` older than the retention period; never touch other files. `0` disables remote cleanup.

Credentials: never commit the service-account JSON (add to `.gitignore`), store outside the repo (e.g. `/opt/myapp/secrets/`), never log credentials or tokens.

### Workflow

Load settings → Validate enabled destinations → Create local backup → Upload to Drive (if enabled) → Send email (if enabled) → Clean old local backups (`BACKUP_RETENTION_DAYS`) → Clean old Drive backups (if enabled) → Report.

Destinations are independent: one failing must not stop the other. Exit non-zero if the backup or any enabled destination failed. Keep the local file when a destination fails.

### Failure handling

- Backup creation fails + email enabled → send a failure alert (no secrets, credentials or full stack traces).
- Drive upload fails + email enabled → the email states the Drive upload failed.
- Sending the alert never raises; log instead. Use `logging` for every step, never `print()`.

### Scheduling (choose one, never both)

- **systemd timer** (no Celery): `deploy/systemd/templates/backup.service.template` + `backup.timer.template`, `Type=oneshot`, `EnvironmentFile=${BACKEND_PATH}/.env`, `OnCalendar` from `BACKUP_CRON_HOUR`/`BACKUP_CRON_MINUTE`, `Persistent=true`.
- **Celery Beat** (only when `CELERY_ENABLED` and `CELERY_BEAT_ENABLED` are True): task `apps.backups.tasks.backup_database`, `crontab(hour=BACKUP_CRON_HOUR, minute=BACKUP_CRON_MINUTE)`, calls the service only, no automatic Celery retry.

### Docker

With PostgreSQL the backend image includes `postgresql-client` whose major version matches the server. `BACKUP_DIR` is a mounted volume. The Google service-account file is mounted read-only as a secret, never copied into the image.

### Security

Backups contain the full database — treat as secrets. `BACKUP_DIR` must never be served by Nginx or exposed via `/media/` or `/static/`; restrict its permissions to the backend service user. Prefer Drive over email in production (email for small DBs/notifications). Never log DB passwords, SMTP passwords, Google credentials, refresh tokens or backup contents.

### Restore documentation (README)

```bash
# SQLite
gunzip -c <file>.sqlite3.gz > db.sqlite3
# PostgreSQL
pg_restore --clean --no-owner -d <database> <file>.dump
```

A backup system isn't complete until a restore has been tested.

### Backup tests

No real email or Google calls: use `django.core.mail.backends.locmem.EmailBackend`, `unittest.mock` for the Drive client and subprocess, `tmp_path` for `BACKUP_DIR`.

Required: `test_sqlite_backup_creates_valid_compressed_file`, `test_postgresql_password_passed_via_env_not_arguments`, `test_postgresql_failure_removes_partial_file`, `test_unsupported_engine_raises_error`, `test_email_sent_when_email_flag_enabled`, `test_email_not_sent_when_email_flag_disabled`, `test_large_backup_not_attached`, `test_drive_upload_when_drive_flag_enabled`, `test_drive_not_called_when_drive_flag_disabled`, `test_drive_not_imported_when_disabled`, `test_both_destinations_enabled_email_contains_drive_link`, `test_drive_failure_still_sends_email_and_exits_non_zero`, `test_missing_required_setting_fails_fast`, `test_backup_failure_sends_alert_email`, `test_local_retention_removes_only_old_backup_files`, `test_drive_retention_deletes_only_prefixed_old_files`, `test_command_no_email_flag`, `test_command_no_drive_flag`, `test_command_local_only_flag`, `test_command_exit_code_on_failure`.

## Required validation commands

Before finishing:

```bash
python manage.py check
python manage.py makemigrations --check
pytest
pytest --cov=. --cov-report=term-missing
ruff check .            # if configured
docker compose -f docker/local/docker-compose.yml config   # for Docker changes (+ staging/production files when changed)
```

For deployment changes: validate generated Nginx and systemd configs, required env vars, and run the deployment health check.

## Definition of done

A feature is complete only when:
- Requirement understood; correct app identified.
- Model + migration (if needed), serializer, business logic (services/selectors), view/viewset, URL, permission and validation implemented.
- Standard response format and centralized exception handling verified.
- Tests and useful fixtures added; coverage checked; existing tests pass.
- OpenAPI updated (incl. 429 where relevant).
- Django checks and migration checks pass.
- Docker, Celery, Nginx, systemd and deploy scripts validated if changed/used.
- Jazzmin configured if applicable; Health API implemented.
- Throttling: global enabled, anon + user throttled, stricter auth/sensitive limits, rates from `.env`, shared cache when scaled, 429 in standard format, tests present, no endpoint unintentionally unthrottled.
- Backup: `backup_db` works for SQLite and PostgreSQL; flags control destinations; disabled destinations never imported/contacted; missing settings fail fast; independent destinations; non-zero exit on failure; local and Drive retention; failure alert; one schedule; `postgresql-client` in image; `.env.example` updated; credentials gitignored; tests use no network; restore documented and tested.
- No secrets or environment-specific values hardcoded or logged.

## Existing project safety rules

Read before changing. Understand existing behavior. Inspect tests, migrations, API contracts, Docker, deployment, Nginx, systemd, Celery and env config. Avoid unnecessary rewrites; make incremental changes; add regression tests; run the existing suite; validate the final architecture; document breaking changes. Never assume an existing project already follows this skill.

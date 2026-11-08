# أبو سمرة (Abo Samra) — Backend

Django REST Framework API for the Abo Samra spice shop e-store (code in `backend/`). The frontend is a separate Vue 3 PWA in `frontend/` (spec: `docs/prompts/frontend-vue-pwa.md`) that consumes this API. Deployment tooling lives in `deploy/` (its own git repo).

## Sources of truth

1. **`docs/prompts/backend-drf.md`** — the domain spec: models, business rules, pricing engine, endpoints, permissions, seed data, tests. Its API contract (paths, field names, status codes, error shapes) is fixed — the Vue app depends on it.
2. **`.claude/skills/drf-backend/SKILL.md`** — engineering conventions: layout, settings split, env vars, throttling, health API, tests, Docker, deployment, DB backups. Load it before any backend work.

**Conflict rule:** conventions → skill wins. API contract & business rules → `docs/prompts/backend-drf.md` wins.

## Project-specific decisions (already resolved)

- **Error format:** `{"detail": "...", "code": "..."}` for general errors, DRF-default `{"field": ["..."]}` for validation — NOT the skill's `success/message/data` envelope. Successful responses return the resource directly (no envelope). The centralized exception handler in `common/` emits this format, including 401/403/404/429.
- **Messages:** all user-facing errors in Egyptian Arabic.
- **Layout:** Django project root is `backend/` (so `apps/`, `config/`, `common/` live under it).
- **Apps:** `apps/core`, `apps/accounts`, `apps/catalog`, `apps/offers`, `apps/orders` (+ `apps/backups` from the skill).
- **API base:** `/api/v1/`; health at `/api/health/`; schema at `/api/schema/`, docs at `/api/docs/`.
- **Auth:** custom `accounts.User` with `phone` as `USERNAME_FIELD` (set `AUTH_USER_MODEL` before the first migration). Customers: phone-only login, no OTP, no password. Staff: phone + password. Token lifetimes per the spec (customer refresh 60 days, staff 7 days).
- **Throttle scopes:** `auth` 10/min on register + both logins, `quote` 60/min, `orders` 10/min per user — all rates from `.env`.
- **Products soft delete:** use `is_archived` per the spec for products that have order lines.
- **Money:** `DecimalField(10, 2)`, rounded to whole pounds in responses, round half up.
- **Locale:** `LANGUAGE_CODE="ar"`, `TIME_ZONE="Africa/Cairo"`, `USE_TZ=True`.
- **Python:** 3.12 (spec) — keep Docker image and CI on 3.12.

## Commands

```bash
make install-dev
make migrate
python manage.py seed_abo_samra
make test
make docker-local
```

## Before finishing any task

```bash
python manage.py check
python manage.py makemigrations --check
pytest --cov=. --cov-report=term-missing
ruff check .
```

The pricing reference case in the spec (subtotal 435, discount 32, delivery 30, total 433, remaining 97) must always pass.

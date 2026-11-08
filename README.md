# Abo Samra (أبو سمرة)

Spice shop e-store: Django REST Framework API (`backend/`) + Vue 3 RTL PWA (`frontend/`).
Deployment tooling lives in `deploy/` (separate git repo, not tracked here). Plan: `docs/plan/`.

## Backend (Python 3.12)

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
make install-dev
cp .env.example .env
make migrate
python manage.py seed_abo_samra
make run            # http://localhost:8000/api/docs/
make test
```

Checks before finishing: `python manage.py check`, `makemigrations --check`, `pytest --cov=.`, `ruff check .`.

## Frontend (Node 22)

```bash
cd frontend
npm ci
cp .env.example .env     # VITE_USE_MOCKS=true runs against the MSW mock API
npm run dev              # http://localhost:5173
npm run lint && npm run type-check && npm test && npm run build
```

## End-to-end tests (Playwright)

```bash
cd frontend
npx playwright install chromium
npm run e2e                                  # MSW mock mode via the vite dev server
E2E_BASE_URL=http://localhost:5173 E2E_USE_MOCKS=false npm run e2e   # real API
```

## CI

`.github/workflows/backend-ci.yml` and `frontend-ci.yml`, each scoped to its directory.

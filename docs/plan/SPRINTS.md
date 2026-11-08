# Sprint Plan

Repo layout: `backend/` (Django root: apps/, config/, common/), `frontend/` (Vue 3 PWA; `frontend/e2e` Playwright), `docs/`, `deploy/` (separate git repo; tooling only, never run without user confirmation).

Two parallel tracks: **Backend** (BE-*) and **Frontend** (FE-*). The frontend runs on an MSW mock layer (FE-02) that mirrors the contract in FSPEC 9, so it never waits for the backend. Real-API integration happens in S6 (FE-14). Contract drift: BSPEC wins on API/business rules (CLAUDE.md); a mismatch becomes a task, not a silent workaround.

Task details and acceptance criteria: TASKS.md. Process: WORKFLOW.md.

## S1 - Backend foundation
- Goal: runnable, tested Django skeleton with auth, throttling, health and Docker.
- Tasks: BE-01, BE-02, BE-03, BE-04, BE-05, BE-06, OPS-01, PA-01
- Dependencies: BE-01 -> BE-02/BE-03 -> BE-04 -> BE-05 -> BE-06.
- Parallel: BE-01 || OPS-01 || PA-01; BE-02 || BE-03 after BE-01. (Frontend S4 FE-01..FE-04 may start early, see below.)
- DoD: CLAUDE.md "before finishing" commands green; `docker compose up` serves `/api/health/`; auth contract tests pass; PA traceability matrix exists.

## S2 - Catalog, offers, pricing engine
- Goal: public read API and the pricing engine incl. reference case.
- Tasks: BE-07, BE-08, BE-09, BE-10, BE-11
- Dependencies: BE-07 -> BE-08 -> BE-09 -> BE-10 -> BE-11.
- Parallel: **Frontend FE-01..FE-04 + QA-01 run now** (no backend dependency; they start in the first free slot, nominally S2 wall-clock, tracked as S4 scope).
- DoD: reference case 435/32/30/433/97 green; `/products/` <= 4 queries; public endpoints match BSPEC 5/6 shapes.

## S3 - Orders, admin API, seed, backups
- Goal: complete backend per BSPEC; backend accepted by PA.
- Tasks: BE-12, BE-13, BE-14, BE-15, BE-16, BE-17, QA-05, PA-02
- Dependencies: BE-12 -> BE-13 -> BE-14; BE-15 needs BE-11+BE-13; BE-16 needs BE-15; BE-17 needs BE-06; QA-05 needs BE-16; PA-02 needs QA-05.
- Parallel: BE-14 || BE-15 || BE-17 after BE-13; frontend continues FE-05..FE-08 on mocks.
- DoD: all BSPEC 8 tests pass; `openapi.yaml` committed; seed idempotent; PA-02 clean.

## S4 - Frontend foundation + storefront
- Goal: whole customer flow working on mocks (and on real API once S3 lands).
- Tasks: FE-01, FE-02, FE-03, FE-04, FE-05, FE-06, FE-07, FE-08, QA-01, QA-02, PA-03
- Dependencies: FE-01 -> FE-02/FE-03 (parallel) -> FE-04 -> FE-05 -> FE-06 -> FE-07 -> FE-08; QA-01 after FE-01; QA-02 after FE-08; PA-03 after QA-02.
- Parallel: whole sprint is independent of backend S2/S3 (frontend track).
- DoD: browse -> cart -> signup -> order -> success e2e green; Vitest green; PA-03 clean.

## S5 - Admin UI + PWA
- Goal: admin dashboard and installable offline-capable PWA.
- Tasks: FE-09, FE-10, FE-11, FE-12, FE-13, QA-03, QA-04, PA-04
- Dependencies: FE-09 first; FE-10 || FE-11 || FE-12 || FE-13 in parallel; QA-03 after FE-12; QA-04 after FE-13; PA-04 last.
- DoD: admin e2e + PWA/offline e2e green; PA-04 clean.

## S6 - Integration, QA, PA sign-off, deploy prep
- Goal: real-stack verified, signed off, ready for staging.
- Tasks: FE-14, OPS-02, QA-06, OPS-03, PA-05, then OPS-04 and OPS-05
- Dependencies: FE-14 (needs S3+S5) -> QA-06 -> OPS-03 -> PA-05 -> **user confirmation** -> OPS-04 -> OPS-05. OPS-02 parallel with FE-14.
- DoD: full e2e green on docker backend; Lighthouse targets met; PA sign-off logged; staging deployed ONLY after explicit user confirmation, smoke test passed.

## Parallel tracks summary
| Wall-clock | Backend track | Frontend track | Quality/Ops |
|---|---|---|---|
| Wave 1 | S1 BE-01..06 | FE-01..04 | OPS-01, PA-01, QA-01 |
| Wave 2 | S2 BE-07..11 | FE-05..08 | QA-02 |
| Wave 3 | S3 BE-12..17 | FE-09..13 | QA-05, QA-03, QA-04, PA-02..04 |
| Wave 4 | - | FE-14 | OPS-02, QA-06, OPS-03, PA-05, [confirm] OPS-04, OPS-05 |
Max 2-3 agents at once; never two agents editing the same files.

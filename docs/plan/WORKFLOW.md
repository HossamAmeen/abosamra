# Workflow

## 1. Roles
team leader (plans, reviews, accepts/rejects, owns statuses) | backend-dev | frontend-dev | test-agent (Playwright in `frontend/e2e`, API tests) | pa-agent (business review) | ops.
Layout: `backend/` Django root, `frontend/` Vue app, `frontend/e2e` Playwright, `docs/plan/` this plan.
Sources of truth: CLAUDE.md, BSPEC (docs/prompts/backend-drf.md), FSPEC (docs/prompts/frontend-vue-pwa.md), SKILL (.claude/skills/drf-backend/SKILL.md). Conflict rule: API/business -> BSPEC; conventions -> SKILL.

## 2. Cycle per task
1. Leader assigns task ID (one per agent run) with: TASKS.md row, relevant spec sections, files owned.
2. Dev sets Status `in-progress`, implements, runs checks, sets `in-review`, reports changed files + command output.
3. Leader review checklist:
   - [ ] Matches spec contract (paths, field names, status codes, error shape, Arabic copy verbatim)
   - [ ] Every acceptance criterion in TASKS.md met, with a test where applicable
   - [ ] Tests pass (BE: check, makemigrations --check, pytest --cov, ruff; FE: lint, type-check, vitest, build)
   - [ ] No secrets/credentials/.env committed; config via env
   - [ ] No scope creep, no edits outside owned files, no N+1 on lists
4. Accept -> `accepted`; reject -> `rejected` with numbered feedback in REVIEW_LOG; dev fixes and resubmits (max 3 rounds, then leader re-scopes).
5. Test agent (after acceptance of user-facing work): writes/runs Playwright e2e in `frontend/e2e` (or API tests for backend-only), status `qa`. Failures -> new tasks (BE-xx/FE-xx, next free ID) owned by the responsible dev, parent task reverts to `rejected`/blocked.
6. PA agent reviews the sprint's accepted work against the business checkpoints (section 4), status `pa-review`. Findings -> new tasks.
7. Task `done` when accepted + QA green + PA clean. Sprint closes when all its tasks are `done`.
8. Loop until every task is `done` and PA-05 signs off.

## 3. Status convention
Edit only the Status column in TASKS.md (one commit-sized edit per change). Allowed values: `todo`, `in-progress`, `in-review`, `rejected`, `accepted`, `qa`, `pa-review`, `done`, `blocked`. New tasks from failures are appended with the next ID in their series, with a "Found by" mention in the acceptance column. Devs may set only `in-progress`/`in-review`; leader sets the rest.

## 4. PA business-requirement checkpoints
Backend (BSPEC):
- CP-B1 Phone normalized everywhere (Arabic digits, +20, 0020) and invalid rejected with the Arabic message (4.1)
- CP-B2 Customers register with name+phone, phone-only login, no OTP/password; staff via password; 409/404 semantics (4.2)
- CP-B3 Pricing: reference case 435/32/30/433/97; best single percentage; bundles not discounted; free delivery at threshold (4.3)
- CP-B4 Order creation is atomic, stock decremented by stock_factor, 409 cart_changed, 503 when closed, numbers from 1001 (4.4)
- CP-B5 Status transitions and cancel stock restore, status log (4.5)
- CP-B6 Catalog visibility: unavailable shown as "خلصان" but not orderable; inactive categories hidden (4.6)
- CP-B7 Customers see only their own data; admin endpoints staff-only (4.2, 8)
- CP-B8 Seed data usable immediately; prices placeholders editable by owner (7, 9)
Storefront (FSPEC):
- CP-F1 Browse by category/search/offers on mobile RTL, copy verbatim (6.1-6.4)
- CP-F2 Add to cart via card, stepper, weight-specific product page with notes (6.2, 6.3)
- CP-F3 Cart totals/discounts/delivery come from /cart/quote/ (8)
- CP-F4 Free-delivery progress live (6.5)
- CP-F5 Sign-up/login flows incl. error switching (6.6)
- CP-F6 COD order placement and success with order number (6.5, 6.7)
- CP-F7 Cart survives reload/offline (8)
- CP-F8 Money/digits format, 44px targets, a11y labels (2)
Admin and PWA:
- CP-A1 Owner sees today's orders/sales/pending/low stock (7.1)
- CP-A2 Owner advances/cancels orders; next-action buttons correct (7.2)
- CP-A3 Owner toggles availability instantly, creates product with several weights (7.3, 7.4)
- CP-A4 Owner creates/pauses percentage, bundle, free-delivery offers (7.5)
- CP-A5 Owner finds customers by name/phone with spend stats (7.6)
- CP-A6 Non-staff cannot reach admin (5)
- CP-P1 Installable PWA with manifest values (10)
- CP-P2 Offline browsing works; checkout blocked with message (10)
- CP-P3 Update toast and install prompt behaviours (10)
PA-01 expands these into `docs/plan/PA_CHECKLIST.md` (requirement -> task -> test).

## 5. REVIEW_LOG.md entry format
```
## <YYYY-MM-DD> <TASK-ID> <review-type: leader|qa|pa|ops> <result: accepted|rejected|pass|fail|signed-off>
- Reviewer:
- Round: n
- Evidence: commands run + results / test names / screenshots path
- Findings: 1. ... 2. ...   (each with severity: blocker|major|minor)
- New tasks: <IDs or none>
- Decision / next: ...
```

## 6. Rules
- Deploy happens LAST (OPS-04). It requires PA-05 sign-off AND explicit user confirmation in chat; never run `deploy/` Makefile targets earlier, never commit `deploy/config.yml` secrets.
- Frontend works against MSW until FE-14; backend changes to the contract require leader approval and a matching FE task.
- Commits/pushes only when the user asks.

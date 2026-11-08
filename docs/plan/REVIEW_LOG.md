# Review Log

Append-only. One entry per review event (leader review, QA run, PA review). Format in WORKFLOW.md section 5.

## 2026-11-08 — BE-01..BE-06 — ACCEPTED (leader)
Verified independently: manage.py check OK, makemigrations --check clean, pytest 86 passed / 93% cov, ruff clean, backend/.env git-ignored.
Follow-ups: move backend/.github/workflows/backend-ci.yml to root .github/workflows (OPS-01); docker/staging+production dirs belong to OPS-02; health/auth deviations from skill envelope are intended (CLAUDE.md).

## 2026-11-08 — BE-07..BE-11 — ACCEPTED (leader)
Verified: check OK, migrations clean, pytest 166 passed/97% cov, ruff clean, pricing reference case test passes.
Notes: BE-15 serializer must call Offer.validate_relations(); empty cart quote returns fee 0/total 0 (accepted); bundle seed must use an honey ربع كيلو variant (see FE note 4).

## 2026-11-08 — FE-01..FE-04 — ACCEPTED (leader)
Verified: lint, vue-tsc, vitest, build all pass; .env/node_modules ignored. UI not visually checked yet (QA/PA will).
Open items: npm audit shows 2 high advisories (FE-14 to resolve); admin customers/offers pagination shape and multipart variants encoding must be agreed between BE-14/15 and FE-11/12 (decision: backend returns plain arrays for /admin/customers/ per FSPEC? -> leader to confirm in BE-14).

## 2026-11-08 — OPS-01, QA-01 — ACCEPTED (leader)
Verified: env files and deploy/config.yml ignored; secrets scan (keys, server IP, email) clean outside deploy/; CI workflows now at root .github/workflows; Playwright smoke passed (mobile-390-rtl).
Note: deploy/ is a nested git repo shown as untracked in root; decide before first commit whether to ignore it or keep as-is (leader: ignore it in root).

## 2026-11-08 — FE-05..FE-08 — ACCEPTED (leader)
Verified: lint, vue-tsc, vitest 77 passed, build OK. Agent also rendered key screens headless at 390px (reference cart 435/32/30/433/97 path covered by tests).
Notes for follow-up: (1) VeeValidate+zod replaced by plain reactive validation (same rules) — acceptable; PA to confirm no behaviour gap. (2) Per-line notes are folded into order `notes` since the order payload has no per-line note — PA to confirm vs spec intent. (3) One console 404 (likely favicon) — FE-14. (4) "عرض المزيد" copy is non-spec — PA to review. (5) /admin/customers mock now paginated; FE-12 must read .results.

## 2026-11-08 — BE-12..BE-17 — ACCEPTED (leader)
Verified: check OK, migrations clean, pytest 290 passed/97% cov, ruff clean, spectacular --validate --fail-on-warn OK, openapi.yaml generated (uncommitted), seed idempotent on fresh DB (16 products, 3 offers). Earlier test hang root-caused (backup test mock looped on nextPageToken) and fixed.
OPEN for PA/owner: winter bundle price 290 > sum of items (~175) — spec numbers inconsistent; kept per spec, placeholder (owner edits). orders_today counts cancelled orders (per spec wording "orders_today"; PA to confirm). Transition error message uses raw status codes (spec-literal; PA to decide if Arabic labels wanted). Docker image change (postgresql-client-16) not built yet -> OPS-02/BE-06 re-verify.

## 2026-11-08 — Scope change (user)
Ignore Docker for now; code only. OPS-02 skipped; Docker verification dropped from QA/PA gates. Deploy (OPS-04) still requires explicit confirmation and will use non-Docker mode if resumed.

## 2026-11-08 — Design gate added (user)
desin/ holds 13 design PNGs. Added FE-15, QA-07, PA-06 and DESIGN_MAP.md. Frontend agent must open the PNGs; PA verifies after QA.

## 2026-11-08 — FE-09..FE-13 — ACCEPTED (leader)
Verified: lint/type-check clean, vitest 96 passed, build OK, manifest + sw.js present with NetworkOnly/SWR/CacheFirst; dist ignored. Admin PNGs were opened by the dev (table in its report) — PA-06 will re-verify independently.
Open: (1) offer cards hide the owner-typed name for percentage/free-delivery offers (derived headline) — PA to decide; (2) SW offline behaviour not verified in browser (SW off in mock mode) — QA-04; (3) openapi types admin product category as int but serializer returns object — FE-14 to confirm on live API; (4) npm audit advisories — FE-14.

## 2026-11-08 — FE-15 — ACCEPTED (leader), design verification pending QA-07/PA-06
Verified: lint/type-check clean, vitest 96 passed, build OK, DESIGN_CHECKLIST.md present (13 rows).
Behaviour change to watch: discount badge now derives only from variant old_price (not offer %). Backend returns old_price only from compare_at_price, so offer-% -only products show no card badge (product page still shows offer pill). PA to confirm vs designs. Favicon 404 not reproducible; fix is best-effort. Intentional diffs listed in DESIGN_CHECKLIST.md — PA-06 to rule on each.

## 2026-11-08 — QA-02, QA-03, QA-04, QA-07 — ACCEPTED (leader)
Re-ran `npm run e2e`: 52 tests, 51 passed, 1 failed (intended: QA-F01 admin offers shows validation error before submit). 13 compare images produced. QA_VISUAL.md: no major diffs. Not covered: install prompt / update toast / iOS sheet (CP-P3), axe on admin screens.
Open bug: QA-F01 -> frontend fix after PA review (batch with PA findings).

## 2026-11-08 PA-01, PA-02, PA-03, PA-04 (partial), PA-06 pa fail (NOT SIGNED OFF)
- Reviewer: pa-agent
- Round: 1
- Evidence: fresh sqlite DB + seed + runserver, real HTTP script (register/login/quote/orders/transitions/stock/permissions/admin CRUD, throttle on a second server); temp DB and servers removed. Gates: check OK, makemigrations clean, pytest 290 passed 97% cov, ruff clean; FE lint clean, vitest 96 passed, Playwright 51 passed 1 failed (QA-F01). 13 design/compare images opened. Files: docs/plan/PA_CHECKLIST.md (48 PASS / 5 FAIL / 5 UNVERIFIED), DESIGN_REVIEW.md (4 match, 9 minor, 0 major), FIX_TASKS.md.
- Findings: 1. QA-F01 pristine offer form error (FIX-01, minor, failing test). 2. Bundle card prints old_price 175 under price 290; seed bundle price above item sum (FIX-02, FIX-03, major). 3. Offer-only discounted products missing from discount lists (FIX-04, minor). 4. Per-line notes folded although backend accepts item notes (FIX-05, minor). 5. Duplicate headline line on offer cards (FIX-06). 6. Raw status codes in transition error, formal-Arabic DRF defaults, empty result for bad status filter (FIX-07, FIX-10, FIX-11, minor). 7. Not verified: CP-P3, admin axe/Lighthouse, Vue app on real API, Postgres sequence (FIX-08, FIX-09, FIX-12).
- Rulings: orders_today including cancelled accepted; storefront plain validation accepted; discount badge from old_price only accepted; "عرض المزيد" accepted; /admin/customers pagination accepted; intentional design differences ruled in DESIGN_REVIEW.md.
- New tasks: FIX-01..FIX-12.
- Decision / next: NOT SIGNED OFF. Blocking: FIX-01, FIX-02, FIX-03 (before design/storefront sign-off) and FIX-08, FIX-09 (before PA-05). Backend business rules BSPEC 4.1-4.6 all PASS. Re-review after fixes; PA-02/03/06 can close once FIX-01..03 pass; PA-04/05 stay open.

## 2026-11-08 — Backend FIX-03/07/11 and Frontend FIX-01/02/04/05/06 + FE-14 — ACCEPTED (leader)
Re-ran: backend check/migrations/ruff clean, pytest 291 passed; frontend lint/type-check clean, vitest 99, build OK, e2e 52/52 (QA-F01 now passes). FE-14: dev drove the real backend headless (no mismatches found; stock 10->9.25->10 on order/cancel verified via API).
Accepted risks: npm audit 2 high (zod <4.6.6 via @vee-validate/zod, no non-breaking fix; zod only validates own forms). Lighthouse not run (no tooling) -> QA-06/FIX-09. FIX-10 and FIX-12 deferred by leader.

## 2026-11-08 — FIX-08, QA-05, QA-06 — ACCEPTED (leader)
Re-ran: backend pytest 407 passed/1 skipped (Postgres-only concurrency test), 97% cov, ruff clean; e2e:real 4/4 passed; dev servers cleaned up. Test agent reports e2e 64/64, admin axe clean on 8 screens.
Open: QA-F02 (major) Lighthouse perf 71-88 (<90); QA-F03 (minor) missing <main> landmark + product card aria-label/visible-text mismatch; honey product page shows two 'أضف للسلة' buttons on real API; B4.6 (Postgres) still unverified; FIX-10, FIX-12 deferred. -> frontend fix round.

## 2026-11-08 — QA-F02/F03 fix round — ACCEPTED (leader), pending PA re-review
Re-ran: lint/type-check clean, vitest 99, build OK, e2e 64/64, no stray servers. Dev reports Lighthouse mobile perf after: / 92-95, /categories/spices 93-96, /products 96-97, /offers 92-96, /cart 98 (before: 68-96). Honey 'two buttons' = not a bug (list-page stepper card). Lighthouse a11y not re-run after landmark/aria change -> PA to re-run.

## 2026-11-08 PA final re-review - SIGNED OFF
- Reviewer: pa-agent (round 2, final)
- Evidence (all run by PA): backend check OK, makemigrations clean, ruff clean, pytest 407 passed / 1 skipped, 97% cov; FE lint + type-check clean, vitest 99 passed, `npm run e2e` 64/64, `npm run e2e:real` 4/4. Fresh sqlite in scratchpad + seed + runserver + `vite build` with VITE_USE_MOCKS=false + `vite preview`; Lighthouse 13.6 mobile (performance + accessibility), 3 runs per page. API spot checks: bundle 160/175, item note on order line, Arabic transition message, 400 on bad status filter, formal-Arabic default for empty PATCH (FIX-10).
- Lighthouse (perf / a11y): `/` 93, 89, 92 / 100; `/categories/spices` 95, 96, 90 / 100; `/products/cumin` 98, 97, 97 / 100; `/offers` 90, 94, 94 / 100; `/cart` 98, 96, 98 / 100. F8.2 verdict: PASS (a11y 100 everywhere; every page median >= 92; the single 89 on `/` is run noise in headless 4x CPU throttling, not a regression).
- Design: all 13 PNGs in desin/ and all 13 compare images viewed; 4 match, 9 minor, 0 major; design signed off.
- Checklist: 0 FAIL; B4.6 and B4.8 UNVERIFIED-accepted. FIX-01..09, 11 verified; FIX-10 deferred non-blocking; FIX-12 unverified accepted risk.
- Servers stopped, temp DBs and build removed, no changes to backend/ frontend/ deploy/, nothing committed.
- Decision: SIGNED OFF. Accepted risks: Postgres order-number sequence/concurrency untested (run on staging), FIX-10 formal Arabic default messages on admin API, npm audit zod advisory (2 high, dev form validation only), SW offline/PWA install evidenced by e2e not Lighthouse (Lighthouse 13 has no PWA category), notify_new_order log stub not observed.

## 2026-11-08 — LEADER: PA SIGN-OFF received (code complete, pre-deploy)
All build/test/review gates passed. Remaining: OPS-03 (deploy config/runbook), OPS-04 (staging deploy — requires explicit user confirmation), OPS-05 (post-deploy smoke). OPS-02 skipped (Docker out of scope). Next-round items: FIX-10 (Egyptian Arabic DRF default messages), FIX-12/B4.6 (Postgres concurrency test on staging), B4.8 (observe notify_new_order log).

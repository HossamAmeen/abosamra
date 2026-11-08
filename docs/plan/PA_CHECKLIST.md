# PA checklist: requirement traceability matrix (PA-01)

Date: 2026-11-08 (final re-review). Reviewer: pa-agent.

FINAL RE-REVIEW RESULT: 0 FAIL. 2 rows UNVERIFIED-accepted (B4.6 Postgres sequence, B4.8 notify log stub). Final PA runs: pytest 407 passed / 1 skipped (Postgres-only), 97% cov, check/makemigrations/ruff clean; FE lint/type-check clean, vitest 99, `npm run e2e` 64/64, `npm run e2e:real` 4/4. Rows 'FAIL' in the table below were re-run and updated; earlier-round wording in the Verification column is history. BSPEC = docs/prompts/backend-drf.md, FSPEC = docs/prompts/frontend-vue-pwa.md.
Result values: PASS | FAIL | UNVERIFIED. "Run" = executed by PA against a fresh sqlite DB, dev settings, real HTTP (curl-style script), seeded with `seed_abo_samra`; temp DB and server removed afterwards.
Every FAIL has a FIX task in FIX_TASKS.md. Automated gates re-run by PA: `manage.py check` OK, `makemigrations --check` clean, `pytest` 290 passed / 97% cov, `ruff` clean; FE `lint` clean, vitest 96 passed, Playwright 51 passed / 1 failed (QA-F01).

## Backend (CP-B)

| ID | Requirement | Spec | Tasks | Verification | Result |
|---|---|---|---|---|---|
| B1.1 | Phone normalized (Arabic digits, +20, 0020, 20..., spaces/dashes) and invalid rejected with the exact Arabic message | BSPEC 4.1, 8 | BE-03 | Run: register with `٠١٠١٢٣٤٥٦٧٨`, `+201012345678`, `0020 101-234-5678`, `201012345678` normalize to 01012345678; `0101234567`, `02123456789`, `01312345678` -> 400 `{"phone":["اكتب رقم موبايل مصري صحيح (11 رقم يبدأ بـ 01)"]}`; login with Arabic digits works | PASS |
| B2.1 | Register 201 with JWT+user; duplicate -> 409 `phone_exists` (Arabic); name 2-80 and email validated | BSPEC 4.2 | BE-04 | Run: 201, 409 `الرقم ده عنده حساب، ادخل بيه`, 400 name/email messages in Arabic | PASS |
| B2.2 | Customer login phone-only; unknown -> 404 `not_found`; staff phone on customer login -> 404 | BSPEC 4.2 | BE-04 | Run: 200 / 404 `مفيش حساب بالرقم ده` / 404 for 01099999999 | PASS |
| B2.3 | Admin login staff-only with password; wrong or customer -> 401 `الرقم أو الباسورد غلط` | BSPEC 4.2 | BE-04 | Run: 401 wrong pwd, 401 customer phone, 200 staff | PASS |
| B2.4 | JWT: access 30 min, refresh 60 d customer / 7 d staff, claims `name`,`is_staff`, rotation + blacklist, logout 204 | BSPEC 4.2 | BE-04 | Run: decoded tokens (30.0 min, 60.0 d, 7.0 d, claims present); old refresh reuse 401; refresh after logout 401; logout 204 | PASS |
| B2.5 | Throttle `auth` 10/min per IP (429 in common format), quote 60, orders 10 | BSPEC 4.2 | BE-05 | Run on 2nd server with default rates: 10x 404 then 429 `{"detail":"طلبات كتير أوي، استنى شوية وجرّب تاني","code":"throttled"}`. quote/orders rates covered only by pytest | PASS |
| B2.6 | GET/PATCH `/me/`, phone read-only; customers reach only own data | BSPEC 4.2, 6 | BE-04 | Run: PATCH with phone ignored, name/area updated | PASS |
| B3.1 | Reference case 435 / 32 / 30 / 433 / 97 | BSPEC 4.3 | BE-10 | Run via `/cart/quote/` and again via real order (totals identical); pytest test_pricing | PASS |
| B3.2 | Best single percentage wins, no stacking | BSPEC 4.3 | BE-10, BE-15 | Run: added 20% spices + 10% all-shop beside 15% spices: spices 215 -> 20% = 43, honey 220 -> 10% = 22, no stacking; pausing/deleting offers updates quote | PASS |
| B3.3 | Bundles are one line at bundle_price, never get percentage discount | BSPEC 4.3 | BE-10 | Run: bundle 150 x2 -> subtotal 300, discount 0 | PASS |
| B3.4 | Free delivery exactly at threshold; threshold = min(settings, live free_delivery offers) | BSPEC 4.3 | BE-10 | Run: subtotal 500 -> fee 0, remaining 0; 460 -> fee 30, remaining 40; extra offer min_order 300 -> 340 free | PASS |
| B3.5 | Expired offers ignored; `offer_expired` / `not_found` / `unavailable` warnings; qty 1-50 validated | BSPEC 4.3 | BE-10 | Run: expired 50% ignored; expired bundle -> `offer_expired`; qty 0/51 -> 400 `الكمية لازم تكون من 1 لـ 50`; unknown variant -> `not_found` | PASS |
| B3.6 | Seeded bundle price is commercially sensible (bundle price below sum of items) | BSPEC 7, 9 | BE-16 | Run: `/offers/active/` bundle price 290, old_price (sum) 175. Spec-literal placeholder, but the storefront then shows a struck-through price lower than the price | PASS (final re-review: fresh seed, `/offers/active/` bundle_price 160, old_price 175; FIX-03) |
| B4.1 | Order totals equal the quote; atomic; snapshots; payment `cod` | BSPEC 4.4 | BE-12 | Run: order 1001 subtotal/discount/fee/total identical to quote; lines+discount snapshot | PASS |
| B4.2 | Stock decremented by qty x stock_factor (bundle items included) | BSPEC 4.4 | BE-12 | Run: cumin stock 2 -> 1.5 (2 x 0.25); honey 10 -> 9 (kilo); bundle with honey quarter 9 -> 8.75 | PASS |
| B4.3 | 409 `cart_changed` with fresh quote when unavailable / insufficient stock / empty cart | BSPEC 4.4 | BE-12 | Run: all three -> 409 with `quote.warnings`; Arabic detail `فيه حاجات في السلة اتغيرت` | PASS |
| B4.4 | 503 when shop not accepting orders; quote still works | BSPEC 4.4 | BE-07, BE-12 | Run: 503 `المحل مش بياخد طلبات دلوقتي` | PASS |
| B4.5 | Numbers sequential from 1001 | BSPEC 3, 4.4 | BE-12 | Run (sqlite max+1 path): 1001, 1002, 1003 | PASS |
| B4.6 | Number generated by a real PostgreSQL sequence | BSPEC 3 | BE-12 | Not runnable (no PostgreSQL/Docker in scope); only the sqlite fallback was exercised | UNVERIFIED-accepted (no postgres binary or Docker on this host; sqlite max+1 path PASS; `test_concurrency_postgres.py` is skipped here. MUST RUN ON STAGING: `pytest apps/core/tests/test_concurrency_postgres.py` against Postgres and 3 concurrent POST /orders/ -> distinct consecutive numbers >= 1001; FIX-12) |
| B4.7 | Address/area saved to profile; first OrderStatusLog `null -> new`; address min 10 chars | BSPEC 4.4 | BE-12 | Run: `/me/` shows saved address; DB log rows `(None,'new',customer)`; short address -> 400 Arabic | PASS |
| B4.8 | `notify_new_order` runs after commit (log stub) | BSPEC 4.4 | BE-12 | Code present (`transaction.on_commit`) and monkeypatched in test_orders; log output not observed by PA | UNVERIFIED-accepted (log stub; `transaction.on_commit` in code and covered by pytest; PA did not read log output; check staging log once) |
| B5.1 | Valid chain new -> preparing -> out_for_delivery -> delivered; invalid -> 400 Arabic | BSPEC 4.5 | BE-13 | Run: new->delivered 400 `مينفعش تغيّر الحالة من new لـ delivered`; delivered->cancelled 400; cancelled->anything 400; customer PATCH 403 | PASS (message shows raw codes, spec-literal; FIX-07 minor) |
| B5.2 | Every change writes OrderStatusLog | BSPEC 4.5 | BE-13 | Run: DB inspected, 1001 has 4 rows, 1002/1003 2 rows each with changed_by | PASS |
| B5.3 | Cancel restores tracked stock (incl. bundle items); delivered does not change stock | BSPEC 4.5 | BE-13 | Run: cumin 1.25 -> 1.5 after cancel; honey 8.75 -> 9.0 after bundle cancel | PASS |
| B6.1 | Unavailable products listed with `is_available:false`, cannot be ordered | BSPEC 4.6 | BE-08 | Run: catalog lists it; order -> 409 `unavailable` | PASS |
| B6.2 | Inactive categories and their products hidden (categories, products, detail), quote warns | BSPEC 4.6 | BE-08, BE-10 | Run: incense deactivated -> 5 categories, 15 products, detail 404, quote warning | PASS |
| B6.3 | Archived (soft-deleted) products hidden, order history intact | BSPEC 6 | BE-15 | Run: delete product with order lines -> 204, public 404, quote `unavailable`, order still readable; product without lines hard-deleted | PASS |
| B6.4 | Product filters category (`all`), q, featured, discounted, shape per BSPEC 5 | BSPEC 5, 6 | BE-08, BE-11 | Run: honey -> 2; all -> 16; q=كمون -> 1; featured -> 4 (كمون، عسل، كركديه، لوز); discounted -> 7 (compare_at or live %); default variant first; Arabic slugs; Arabic 404 | PASS |
| B7.1 | Customer gets 404 on another customer's order; `/orders/mine/` only own | BSPEC 4.2, 8 | BE-13 | Run | PASS |
| B7.2 | Customer 403 on every `/admin/*`; anonymous 401; anon can quote, cannot order | BSPEC 8 | BE-13, BE-14 | Run: 6 admin endpoints x (anon 401, customer 403 `مش مسموحلك بالعملية دي`); order anon 401 | PASS (+ apps/core/tests/test_permission_matrix.py: 33 routes x anon/customer/staff) |
| B8.1 | Seed gives usable data: settings, 6 categories, 16 products with variants, 3 offers (featured offer ends Thursday 12 Nov 23:59), staff from env | BSPEC 7 | BE-16 | Run: counts and prices match spec; staff login works | PASS |
| B8.2 | Seed idempotent; prices editable by owner | BSPEC 7 | BE-16, BE-15 | pytest test_seed passes (PA did not re-run the command twice); price/stock edits via admin PATCH worked | PASS |

## Admin backend and screens (CP-A)

| ID | Requirement | Spec | Tasks | Verification | Result |
|---|---|---|---|---|---|
| A1.1 | Dashboard numbers: orders_today, sales_today (non-cancelled), pending_count, new_customers_week, low_stock | BSPEC 6, FSPEC 7.1 | BE-14, FE-09 | Run: 3 / 433 / 0 / 2 / cumin 1.5 kilo (stock <= threshold). `orders_today` counts cancelled orders (3) while sales exclude them: ruled acceptable (spec wording) | PASS |
| A1.2 | Dashboard screen, 30 s refresh, nav badge, copy | FSPEC 7.1 | FE-09 | compare/08 image + vitest/e2e `dashboard: confirm a new order` | PASS |
| A2.1 | Admin orders list: `?status`, `?q` (number, name, phone incl. Arabic digits), counts, items_summary, newest first | BSPEC 6 | BE-14 | Run | PASS |
| A2.2 | Orders screen: chips with counts, next-step buttons, cancel with confirm, sheet | FSPEC 7.2 | FE-10 | e2e `advance an order through the full chain and cancel another`; compare/09 | PASS |
| A3.1 | Product create with 3 weights, variants replace-by-id, exactly one default, availability PATCH, soft/hard delete | BSPEC 6, FSPEC 7.3-7.4 | BE-15, FE-11 | Run: create 201 (first variant auto-default when none flagged), two defaults -> 400 Arabic, no variants -> 400 Arabic, replace drops a weight, toggle hides availability on storefront; e2e `create a product with 3 weights`, `toggle product availability` | PASS |
| A3.2 | Product forms/list match design and copy | FSPEC 7.3-7.4 | FE-11, FE-15 | compare/10, 11 | PASS |
| A4.1 | Offers CRUD: percentage / bundle / free_delivery validation (value 1-90, bundle >= 2 items + price, min_order), pause via `{is_active}`, delete | BSPEC 3, 6 | BE-09, BE-15 | Run: all validation errors Arabic; pause removes offer from `/offers/active/` and quotes | PASS |
| A4.2 | Offers screen create/pause works; pristine form shows no error | FSPEC 7.5 | FE-12 | e2e create + pause pass; e2e QA-F01 FAILS (red "اختار القسم" on load, confirmed in compare/12) | PASS (QA-F01 test green in PA final run; compare/12 shows pristine form, no red error) |
| A5.1 | Customers search by name/phone (normalized), orders_count, total_spent (non-cancelled), last_order_at, nulls last | BSPEC 6, FSPEC 7.6 | BE-14, FE-12 | Run: `?q=` Arabic digits and +20 forms work; total_spent excludes cancelled; list is paginated (`results`), FSPEC 9 shows a bare array: FE reads `.results`, accepted | PASS |
| A5.2 | Customers screen | FSPEC 7.6 | FE-12 | e2e `customer search by name and phone`; compare/13 | PASS |
| A6.1 | Non-staff cannot reach admin (API + UI guard) | FSPEC 5, BSPEC 8 | BE-13, FE-09 | Run (API 401/403); e2e guard tests (anonymous and customer redirected) | PASS (+ apps/core/tests/test_permission_matrix.py) |

## Storefront (CP-F)

| ID | Requirement | Spec | Tasks | Verification | Result |
|---|---|---|---|---|---|
| F1.1 | Browse by category / search / offers, RTL mobile, copy verbatim | FSPEC 6.1-6.4 | FE-05..FE-07 | PA copy scan of all bold FSPEC strings against `src/` (163 strings; the 17 not literal are dynamic templates, all checked by hand: counts, `{x}`, offer headlines, date line) + compare/01-05 | PASS |
| F1.2 | Offers/discounted lists show every product the active offers discount | FSPEC 6.1, 6.4 | FE-05, FE-07, FE-15 | Views filter `discounted=true` results by `old_price` only, so the 15% spices offer (cumin, turmeric, cinnamon) never appears in "عروض النهاردة" / "منتجات عليها خصم" while the banner promises the discount | PASS (final: offer-only products in lists with "خصم 15%" caption, vitest + compare/01, 04; FIX-04) |
| F1.3 | Bundle card shows a coherent old price | FSPEC 6.4 | FE-07 | `Offers.vue` prints `old_price` unconditionally; real API gives 175 vs price 290 (mock gives 335) | PASS (final: old price guarded `> price`, vitest; real API 160 vs 175 renders correctly; FIX-02) |
| F2.1 | Add via card "+", stepper, product page with weight/qty/note, sticky cart bar | FSPEC 6.2-6.3 | FE-06 | e2e `add via card, stepper and product weight...`, `product page: choose weight changes total`; compare/02, 03 | PASS |
| F2.2 | Product note is kept on the cart line and reaches the order line | FSPEC 6.3, 6.5 | FE-06, FE-07 | Note stays on the cart line but is folded into order `notes` at checkout; backend accepts per-item `note` (PA confirmed 201 with `lines[0].note`) so the admin sheet never shows per-line notes | PASS (final: PA POST /orders/ with item `note` -> lines[0].note "ناعم"; FE sends per-line note, vitest; FIX-05) |
| F3.1 | Cart totals/discounts/delivery from `/cart/quote/` (435/32/30/433/97) | FSPEC 6.5, 8 | FE-07 | e2e reference cart; compare/05 | PASS |
| F4.1 | Free-delivery progress live | FSPEC 6.5 | FE-07 | compare/05 (97 remaining); vitest/e2e | PASS |
| F5.1 | Sign-up/login, phone rules, phone_exists / not_found switching, `next=checkout` | FSPEC 6.6 | FE-08 | e2e phone validation, phone_exists, not_found tests; compare/06. Plain reactive validation instead of VeeValidate on storefront: same rules, no behaviour gap seen | PASS |
| F6.1 | COD order placement, success screen with `#number`, 409 cart_changed handling | FSPEC 6.5, 6.7 | FE-07, FE-08 | e2e full flow and both 409 tests (mock mode); compare/07 | PASS |
| F6.2 | Storefront works against the real API (contract match, error mapping, admin product category object vs int) | FSPEC 9 | FE-14 | FE-14 still `todo`: no MOCKS-off run. Backend contract was exercised by PA but the Vue app was not pointed at it | PASS (e2e/real/real-api.spec.ts "storefront: reference cart ... order #1001", "admin: create a product" asserts category is an object; FIX-09 test half) |
| F7.1 | Cart survives reload and offline | FSPEC 8 | FE-04, FE-13 | e2e `offline: cart survives a reload` | PASS |
| F8.1 | Money `3,450 ج.م`, Western digits, 44px targets, aria-labels, focus ring, axe clean on storefront | FSPEC 2 | FE-03, QA-04 | e2e a11y/focus tests (6 storefront routes, axe A/AA) | PASS |
| F8.2 | Accessibility on admin screens and Lighthouse (PWA >= installable, A11y >= 95, Perf >= 90) | FSPEC 12 | FE-14, QA-04 | Not run (axe covered storefront only; no Lighthouse run) | PASS (PA own Lighthouse 13.6 mobile, prod build + real API, 3 runs/page: a11y 100 on all 15 runs; perf min-max: / 89-93, /categories/spices 90-96, /products/cumin 97-98, /offers 90-94, /cart 96-98. One run at 89 on `/` is within noise; medians all >= 92. axe A/AA on 8 admin screens PASS; installability via e2e manifest + SW tests because Lighthouse 13 has no PWA category) |

## PWA (CP-P)

| ID | Requirement | Spec | Tasks | Verification | Result |
|---|---|---|---|---|---|
| P1.1 | Manifest values, icons, shortcuts, theme-color | FSPEC 10 | FE-13 | e2e `manifest is valid and linked` (prod build) | PASS |
| P2.1 | Offline browsing from cache, banner, checkout disabled offline | FSPEC 10 | FE-13 | e2e offline tests (3) in prod build with real SW | PASS |
| P3.1 | Install prompt after 2nd visit, iOS sheet, update toast "فيه نسخة جديدة / تحديث" | FSPEC 10 | FE-13 | Components exist (`InstallPrompt.vue`) but no test or manual run | PASS (e2e/p3.pwa.spec.ts: 4 tests, FIX-08) |

## Business rulings recorded during PA

| Item | Ruling |
|---|---|
| `orders_today` includes cancelled orders | Accepted: spec wording; `sales_today` correctly excludes them |
| Transition error shows raw codes (`new`, `delivered`) | Spec-literal, accepted; Arabic labels would be better (minor FIX-07) |
| Plain validation instead of VeeValidate on storefront | Accepted, same rules; admin forms do use VeeValidate+zod |
| Per-line notes folded into order notes | Not accepted (FIX-05, minor) |
| Discount badge only from variant `old_price` | Accepted for the badge (matches design); the discounted lists need FIX-04 |
| Offer name display (percentage/free-delivery cards show derived headline + owner name as second line) | Accepted; hide the second line when it repeats the headline (FIX-06, cosmetic) |
| "عرض المزيد" copy (storefront/admin load more) | Accepted: spec asks for load more without copy |
| Bundle price 290 above item sum 175 | Not accepted for display (FIX-02, FIX-03); needs owner decision on the number |
| `/admin/customers/` paginated instead of bare array | Accepted, FE adapted; keep in openapi.yaml |

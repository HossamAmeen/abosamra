# QA findings

Found by the test agent (QA-02/03/04/07) running Playwright against MSW mocks (`npm run e2e`) and a production build with a real service worker.

| ID | Severity | Status | Area |
|---|---|---|---|
| QA-F01 | minor | fixed (e2e green 2026-11-08) | Admin offers form |
| QA-F02 | major | fixed (Lighthouse mobile >= 92 on all 5 pages, 2026-11-08) | Storefront performance (Lighthouse mobile) |
| QA-F03 | minor | fixed (2026-11-08) | Storefront a11y (Lighthouse-only audits) |

## QA-F01 Admin offer form shows a validation error before any input (minor)
- **Screen:** `/admin/offers` (new-offer card, type "خصم %").
- **Repro:** log in as admin (01099999999 / admin123), open `/admin/offers` without touching anything.
- **Expected:** a pristine form shows no errors; errors appear after pressing **نشر العرض** (FSPEC 7.5; same behaviour as the product form, whose errors only show after submit).
- **Actual:** the **على** select has a red border and the red message **اختار القسم** is visible immediately on load.
- **Evidence:** `frontend/e2e/admin.spec.ts` test "offer form shows no validation error before the user submits (QA-F01)" fails (kept failing on purpose); screenshot `frontend/e2e/visual/screens/12-admin-offers.png`.
- **Spec ref:** FSPEC 7.5; DESIGN: `desin/إدارة العروض.png` shows the form without an error.
- **Owner suggestion:** frontend-dev (`views/admin/Offers.vue`, validation `validateOnMount` / error gating).

## QA-F02 Lighthouse performance below 90 on the production build (major)
- **Repro:** `npm run build` with `VITE_USE_MOCKS=false`, `vite preview`, backend seeded on sqlite; `npx lighthouse http://localhost:4175/ --form-factor=mobile` (Lighthouse 13.6.0, Playwright chromium 1254, headless, default mobile throttling).
- **Result:** performance 71 and 80 (two runs of `/`), 88 (`/categories/spices`); target >= 90 (FSPEC 12). Accessibility 98, best-practices 100, SEO 82. Home: LCP 3.4 s, TBT 460-840 ms, FCP 0.8 s, CLS 0, main-thread work 2.3 s (audit failed), total transfer 235 KiB. `vite preview` serves without gzip/brotli, so the production server config may improve this; the main-thread/TBT part is app code (bundle evaluation on a throttled CPU).
- **Owner suggestion:** frontend-dev (split the home bundle, defer non-critical work, preload the LCP element); ops to re-measure behind nginx with compression.
- Note: Lighthouse 13 has no PWA category, so "PWA installable" is evidenced by the e2e manifest + service-worker tests, not a Lighthouse number.

## QA-F03 Lighthouse-only accessibility audits fail (minor)
- axe WCAG A/AA is clean on every storefront and admin screen, but Lighthouse (a11y 98) fails two audits on `/`:
  - `landmark-one-main`: the document has no `<main>` landmark.
  - `label-content-name-mismatch`: product card links such as `<a href="/products/عسل-نحل-طبيعي" aria-label="عسل نحل طبيعي">` whose visible text (price etc.) is not contained in the aria-label (WCAG 2.5.3 label in name).
- **Owner suggestion:** frontend-dev (wrap page content in `<main>`; make the aria-label start with the visible text or drop it).

## Checked and found OK (no finding)
- Reference quote 435 / 32 / 30 / 433 / remaining 97 shows correctly in the cart (QA-02).
- Phone: accepts `01012345678` and Arabic-Indic digits, rejects `0101234567`, `02...`, `013...`; `phone_exists` and `not_found` switching; server-side `409 cart_changed` (simulated race) applies the returned quote and disables checkout.
- Admin guard (anonymous and customer redirected), status chain new -> preparing -> out_for_delivery -> delivered, cancel with confirm, availability toggle reflected on the storefront, product with 3 weights, offer create + pause, customer search.
- Production build: manifest values, icons, shortcuts, theme-color, SW controls the page, `catalog-api` cache, offline browsing + banner, checkout disabled offline, cart survives offline reload, focus ring on the first 8 tab stops, axe (names/labels/ARIA and WCAG 2 A/AA incl. colour contrast) clean on `/`, `/categories/spices`, `/products/:slug`, `/offers`, `/cart`, `/account`.

## Coverage added 2026-11-08
- axe WCAG 2.0/2.1 A+AA now also runs on admin login, dashboard, orders, products, product form (new and edit), offers, customers: zero violations (`e2e/admin-a11y.spec.ts`).
- CP-P3 install card (2nd visit, تثبيت / مش دلوقتي), iOS sheet and update toast (`e2e/p3.pwa.spec.ts`).
- Real backend journeys (`npm run e2e:real`): no contract mismatch found.
- On the product page of the real API, `getByRole('button', {name: 'أضف للسلة'})` matches 2 buttons for honey (the mock data has one); harmless but check there is no duplicated control.

## Coverage gaps (not findings)
- PostgreSQL-only behaviour (sequence-backed order numbers, concurrent orders) still unrun: no PostgreSQL available here.
- Offline test fixtures use a small hand-written API double (`e2e/fixtures/pwa-api.ts`), not the MSW dataset.

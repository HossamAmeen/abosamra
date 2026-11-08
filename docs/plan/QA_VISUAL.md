# QA-07 visual comparison

How: `frontend/e2e/visual/screens.spec.ts` (run with `npm run e2e`). For each screen it saves
- `frontend/e2e/visual/screens/NN-name.png`: 390x844 viewport screenshot (DPR 2, the official capture), and
- `frontend/e2e/visual/screens/NN-name-tall.png`: the same screen with the viewport stretched to the design PNG's height (the PNGs are full-length mockups with the nav pinned at the bottom), used for
- `frontend/e2e/visual/compare/NN-name.png`: side by side, **app on the left, design PNG on the right**.

Mock data (names, totals, order numbers, counts) differs from the PNGs by design and is not listed as a mismatch. Screenshot state: cart screens use cumin x2 + pepper + honey (quote 435/32/30/433).

Cross-cutting observations (all minor)
- C1. Page header bars (TopBar, AdminHeader, SectionHeader titles) sit roughly 8-12 CSS px higher / tighter than the design: the design's first content block starts lower on every screen (clearest on 05, 06, 08, 09, 10, 13).
- C2. Scrollbars/arrows visible in the PNGs are mockup artifacts, ignored.

| # | Screen | Compare image | Observed mismatches | Verdict |
|---|---|---|---|---|
| 1 | الرئيسية `/` | compare/01-home.png | Category tile "أعشاب ومشروبات" is one line in the app vs two lines in the design (tile text slightly smaller/wider); wheat icon differs (known); no cart badge because the cart is empty (design shows 3); C1 | match / minor |
| 2 | الأقسام والمنتجات | compare/02-category.png | Product cards are slightly more compact vertically than the design; cart bar sits above the nav as in the design; nothing else | match / minor |
| 3 | تفاصيل المنتج | compare/03-product.png | Hero icon slightly larger/higher than design; description copy is mock data; otherwise identical layout, sizes and bottom bar | match |
| 4 | العروض | compare/04-offers.png | Bundle item line wording differs (mock: "ينسون + كركديه + عسل نحل", design: "... عسل نحل ربع كيلو"); header brand text slightly larger in the app; C1 | match / minor |
| 5 | السلة | compare/05-cart.png | Discount label is the offer name ("خصم 15% على كل البهارات") vs design "خصم البهارات 15%" (data, intentional); free-delivery amount differs because cart contents differ; C1 | match / minor |
| 6 | إنشاء حساب | compare/06-account.png | Primary button reads "إنشاء الحساب" on an empty cart vs "إنشاء الحساب وتأكيد الطلب" in the design (documented in DESIGN_CHECKLIST #6); C1 | minor |
| 7 | تم الطلب | compare/07-order-success.png | Same layout/copy; order number differs (data); title block ~6 px tighter than design | match |
| 8 | لوحة التحكم | compare/08-admin-dashboard.png | Layout, tiles, quick buttons, order card and low-stock rows match; app shows 1 pending order vs 3 in design (data); order card omits the area line shown only on the Orders screen; C1 | match / minor |
| 9 | الطلبات | compare/09-admin-orders.png | Chips, order card and buttons match; the app's order card has an extra hairline and slightly tighter row spacing; the area is shown (empty in mock for seed order 1001) | match / minor |
| 10 | المنتجات | compare/10-admin-products.png | Matches (search, chips, toggle, edit button); long names wrap in the design but not in the app (data); C1 | match |
| 11 | إضافة منتج | compare/11-admin-product-new.png | Category is unselected ("اختار القسم") vs preselected "بهارات" in the design (documented); app has extra optional stock fields below the toggles (spec); add-weight dashed button is slightly smaller | match / minor |
| 12 | إدارة العروض | compare/12-admin-offers.png | **Pristine form already shows a red "اختار القسم" error on the على select (finding QA-F01)**; start date is prefilled with today and the featured-offer checkbox exists (spec features not in the PNG); each current-offer card shows an extra name line; form values empty vs sample in design | minor diff (1 finding) |
| 13 | الزبائن | compare/13-admin-customers.png | Matches (avatar, contact lines, call button, stats line); only two seed customers vs five in the design (data); C1 | match |

Summary: 0 major diffs; 11 match / minor, 1 minor (06), 1 minor with a real defect (12, QA-F01).

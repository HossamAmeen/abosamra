# Design map — `desin/*.png` (source of visual truth)

Design PNGs are in `/media/hossam/Software5/startups/abosamra/desin/`. The specs' tokens/copy still apply; where a PNG differs visibly (layout, spacing, order, icon, copy), the PNG wins and the difference is logged in REVIEW_LOG.md.

| Design file | Route | Task owner |
|---|---|---|
| الرئيسية.png | `/` | FE-05 |
| الأقسام والمنتجات.png | `/categories/:slug` | FE-06 |
| تفاصيل المنتج.png | `/products/:slug` | FE-06 |
| العروض.png | `/offers` | FE-07 |
| السلة.png | `/cart` | FE-07 |
| إنشاء حساب.png | `/account` | FE-08 |
| تم الطلب.png | `/orders/:id/success` | FE-08 |
| لوحة التحكم – الرئيسية.png | `/admin` | FE-09 |
| الطلبات.png | `/admin/orders` | FE-10 |
| المنتجات.png | `/admin/products` | FE-11 |
| إضافة منتج.png | `/admin/products/new` | FE-11 |
| إدارة العروض.png | `/admin/offers` | FE-12 |
| الزبائن.png | `/admin/customers` | FE-12 |

## Gates
1. Dev (FE-15): open every PNG (Read tool), compare against the running screen at 390x844, fix differences; write `docs/plan/DESIGN_CHECKLIST.md` (screen, PNG, what was compared, differences fixed/remaining).
2. QA (QA-07): Playwright captures a 390x844 screenshot of every screen (`frontend/e2e/visual/`, saved to `frontend/e2e/visual/screens/`), side-by-side with its PNG into `frontend/e2e/visual/compare/` and reports mismatches.
3. PA (PA-06): independently opens each PNG and each screenshot, scores per screen (match / minor diff / major diff) in `docs/plan/DESIGN_REVIEW.md`. Any major diff becomes a new FE fix task; loop until all 13 screens are match/minor and PA signs off.

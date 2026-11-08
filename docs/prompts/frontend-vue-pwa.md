# Build Prompt — "أبو سمرة" Spice Shop Store (Vue 3 PWA)

You are building the **frontend** of a small e-store for **أبو سمرة (Abo Samra)**, a traditional Egyptian spice & herb shop (عطارة) in Cairo. The backend is a separate **Django REST Framework** project; this prompt defines the API contract the frontend expects (Section 9) — do not build the backend here.

The app has two parts in **one** Vue project:
1. **Storefront** (customers) — browse categories/products, offers, cart, sign up with name + phone (email optional), place cash-on-delivery orders.
2. **Admin dashboard** (shop owner) — orders, products, offers, customers. Also mobile-first.

Everything is **Arabic, RTL, mobile-first** (designed at 390 px wide). It must be an installable **PWA**.

Follow this document exactly for colors, sizes, copy and button placement. All UI copy below is final Arabic (Egyptian dialect) — use it verbatim.

---

## 1. Tech stack

- **Vue 3** (`<script setup>`, Composition API) + **TypeScript** + **Vite**
- **Vue Router 4** (history mode), **Pinia** (+ `pinia-plugin-persistedstate` for cart & auth)
- **Tailwind CSS** with the design tokens below in `tailwind.config` (no other UI library)
- **vite-plugin-pwa** (Workbox, `registerType: 'prompt'`)
- **axios** with one API client + interceptors (JWT, 401 refresh)
- **lucide-vue-next** for icons (stroke icons, 2px stroke, matches the design)
- **@fontsource/cairo** (weights 400, 600, 700, 800) — self-hosted so the font works offline
- **VeeValidate + zod** for forms
- **dayjs** with `ar` locale for dates
- Lint/format: ESLint + Prettier. Tests: Vitest for stores/utils, Playwright smoke test for the order flow.

## 2. Global rules

- `<html lang="ar" dir="rtl">`. Use logical CSS properties (`ps-`, `pe-`, `ms-`, `me-`, `start`, `end`) — never hard-code left/right.
- Phone numbers, emails and prices with Latin digits render inside `dir="ltr"` spans where needed. Use **Western digits** everywhere (`60 ج.م`), not Arabic-Indic.
- Money format: `Number(n).toLocaleString('en-US') + ' ج.م'` → `3,450 ج.م`. Discounts shown as `- 32 ج.م`.
- Max content width 480 px, centered, so it still looks like the phone design on tablets/desktop. Admin may go up to 720 px.
- **Touch targets ≥ 44×44 px.** Real `<button>`, `<a>`, `<input>` + `<label>`. `aria-label` on every icon-only button (Arabic). Visible focus ring: `2px solid #A3510F`, offset 2px.
- Text contrast ≥ 4.5:1 (all token pairs below pass — don't invent lighter greys).
- Bottom navigation is fixed; page content scrolls between the top header and the bottom nav. Respect `env(safe-area-inset-bottom)`.
- Loading: skeleton blocks in `#F1DFCC` with a subtle pulse. Errors: inline danger text + retry button. Empty states: icon + one line + action.
- No emoji anywhere in the UI.

## 3. Design tokens

### Colors
| Token | Hex | Use |
|---|---|---|
| `primary` | `#F7A04B` | Logo circle, primary buttons, header band, add buttons, active weight border |
| `primary-soft` | `#FFE6CC` | Active nav pill, steppers background, badges, highlighted stat card |
| `primary-tint` | `#FFF1E2` | Icon-button backgrounds, secondary buttons, upload box |
| `link` | `#A3510F` | Links, active nav icon/label, focus ring. Hover `#7A3A08` |
| `brand-deep` | `#7A3A08` | Text on `primary-soft`/`primary-tint` badges & secondary buttons |
| `ink` | `#3B2412` | Main text; text on `primary` buttons; dark banners/selected chips background |
| `ink-2` | `#5A3B26` | Secondary body text, descriptions |
| `muted` | `#6E5040` | Captions, units, inactive nav, strikethrough old price |
| `bg` | `#FFF8F1` | App background |
| `surface` | `#FFFFFF` | Cards, header bar, bottom nav, inputs |
| `border` | `#F1DFCC` | Card borders, dividers |
| `input-border` | `#E3CCB4` | Inputs, unselected chips |
| `dashed` | `#E3B98E` | Dashed borders (upload, "add weight") |
| `on-dark` | `#FFF8F1` | Text on `ink` backgrounds; sub-text on dark banner `#F3DCC6` |
| `success` | `#2F6B3A` on `#E3F1E1` (strong text `#234F2B`) | "متوفر", added-to-cart, free delivery, switch ON |
| `danger` | `#B3261E` (soft bg `#FDE7E5`) | Discount badges, cart badge, remove, low stock |
| `disabled` | bg `#EADBCB`, text `#6E5040` | Disabled primary button |
| `switch-off` | `#B9A694` | Switch track OFF |

Category tints (thumb/icon backgrounds), icon stroke color `#6B3E1C`:
| Category | slug | Tint | Icon (lucide) |
|---|---|---|---|
| بهارات | `spices` | `#F6D9B8` | bowl / `soup` |
| أعشاب ومشروبات | `herbs` | `#DCEBCF` | `leaf` |
| عسل وزيوت | `honey` | `#F9E4A8` | `droplet` |
| مكسرات | `nuts` | `#EBD7C3` | `nut` |
| بقوليات وحبوب | `grains` | `#F2E6C9` | `wheat` |
| بخور | `incense` | `#E6DAEE` | `flame` |
Tint and icon come from the API (`category.color`, `category.icon`) with these as defaults.

Order status pills (bg / text):
- `new` جديد — `#FFE6CC` / `#7A3A08`
- `preparing` بيتجهز — `#FFF4C2` / `#6B5200`
- `out_for_delivery` في الطريق — `#DDEBFA` / `#1F4E7A`
- `delivered` اتسلم — `#E3F1E1` / `#2F6B3A`
- `cancelled` اتلغى — `#FDE7E5` / `#B3261E`

### Typography — Cairo
| Role | Size / weight |
|---|---|
| Page title (h1) | 22 / 800 (product name 26 / 800, success title 26 / 800) |
| Section title (h2) | 18 / 800 |
| Banner headline | 21–22 / 800 |
| Body | 15 / 400, line-height 1.7 for paragraphs |
| Product name | 15 / 700 |
| Price | 16 / 800 (totals 18–20 / 800) |
| Caption / unit | 12–13 / 600, color `muted` |
| Buttons | primary 16 / 800; chips & small buttons 14 / 700 |
| Nav labels | 12 / 700 |

### Shape & spacing
- Radius: cards 16, banners 20, primary buttons 14, inputs & small buttons 12, chips/pills/badges 999, header band bottom corners 24, product thumb 12.
- Page padding 16 px; gap between sections 20 px; between cards 12 px; inside cards 8–14 px.
- Primary button: height 52, full width, bg `primary`, text `ink` 16/800, radius 14, optional leading icon 20 px, gap 8.
- Input: height 50, border 1px `input-border`, radius 12, padding-inline 14, 15 px text, bg white. Label above (14/700), gap 6.
- Card: bg white, 1px `border`, radius 16, no shadow.
- Chip: height 44 (admin 40), padding-inline 14–16, pill. Selected = bg `ink`, text `on-dark`, border `ink`. Unselected = white, `input-border` border, `ink` text. Horizontal scroll row, no scrollbar.
- Switch: track 48×28 pill, knob 22 px white; ON = `success` track, knob at the end; OFF = `switch-off`, knob at start. Label next to it (12/700): green when ON, `muted` when OFF. `role="switch"` + `aria-checked`.
- Stepper: pill bg `primary-soft`; "+" = 44 px circle bg `primary`; "−" = 44 px circle bg white; qty 16–18/800 in between. In RTL the "+" sits on the **right** (start).

### Logo
Circle (44–48 px; 84 px on sign-up) filled `primary` with a `leaf` icon in `ink` (55% of circle size). Next to it: **أبو سمرة** (20/800) and under it the subtitle (12/600, `ink-2`): **عطارة وبهارات** in the storefront, **لوحة التحكم** in admin. Inside the orange header band, the circle is **white** instead. PWA icon = same leaf on the orange circle (generate 192, 512 and maskable 512).

## 4. Shared components

- `AppLogo` (props: size, variant `store|admin`, onOrange)
- `BottomNav` (store / admin items, active state = pill bg `primary-soft`, icon+label color `link`; inactive `muted`; item min 64×52; optional count badge)
- `TopBar` (back button on the **start/right** side: 44 px circle bg `primary-tint` with `chevron-right`; title 20/800; optional action on the end/left)
- `AdminHeader` (white bar: logo with "لوحة التحكم" on the start side, page action on the end side; under it page h1 22/800)
- `ProductCard` (variants: `round-add` and `stepper`), `CategoryTile`, `PriceTag` (price + optional strikethrough old price), `DiscountBadge` (`-14%`, red, top-start corner of thumb, `dir="ltr"`)
- `QtyStepper`, `ChipRow`, `ToggleSwitch`, `SectionHeader` (h2 on start, "عرض الكل" link on end), `OfferBanner` (dark / soft / success variants), `StatusPill`, `EmptyState`, `Toast` (success green, `role="status"`, 3 s)
- `ProductThumb` — product image if present, else category tint + category icon (40 px, stroke `#6B3E1C`).

## 5. Routes

Storefront (layout: `StoreLayout` with `BottomNav`):
| Path | Screen | Nav active |
|---|---|---|
| `/` | Home | الرئيسية |
| `/categories/:slug?` | Category listing (default `spices`; `all` = كل المنتجات) | الأقسام |
| `/products/:slug` | Product details (no bottom nav) | — |
| `/offers` | Offers | العروض |
| `/cart` | Cart | السلة |
| `/account` | Sign-up / login if guest, else profile + my orders | حسابي |
| `/orders/:id/success` | Order placed | حسابي |

Admin (layout: `AdminLayout`, lazy-loaded chunk, guard: `user.is_staff`):
| Path | Screen | Nav |
|---|---|---|
| `/admin/login` | Phone + password | — |
| `/admin` | Dashboard home | الرئيسية |
| `/admin/orders` | Orders (tab via `?status=`) | الطلبات |
| `/admin/products` | Products list | المنتجات |
| `/admin/products/new`, `/admin/products/:id` | Product form (no bottom nav) | — |
| `/admin/offers` | Offers | العروض |
| `/admin/customers` | Customers | الزبائن |

Store bottom nav (start → end): الرئيسية (`home`) · الأقسام (`layout-grid`) · العروض (`tag`) · السلة (`shopping-cart`, red count badge) · حسابي (`user`).
Admin bottom nav: الرئيسية (`bar-chart-3`) · الطلبات (`package`) · المنتجات (bowl/`soup`) · العروض (`tag`) · الزبائن (`users`).

## 6. Storefront screens

### 6.1 Home `/`
1. **Header band** — bg `primary`, padding 16/16/20, bottom corners radius 24, gap 14:
   - Row: `AppLogo` (white circle, 48 px) on the start side; on the end side a 48 px **white circle cart button** with the cart icon and a red count badge (20 px, top-end corner) → `/cart`.
   - Greeting 16/700: **أهلاً بيك.. عايز تطلب إيه النهاردة؟**
   - Search field: white, height 50, radius 14, search icon at start, placeholder **دوّر على كمون، عسل، ينسون...**. Typing (debounced 300 ms) shows results in a dropdown list; Enter → `/categories/all?q=`.
2. **Offer banner** (featured offer from API) — bg `ink`, radius 20, padding 18, whole card is a link → `/offers`. Start side: small pill **عرض الأسبوع** (bg `primary`, text `ink`, 12/700), headline 21/800 `on-dark` e.g. **خصم 15% على كل البهارات**, sub-line 13 px `#F3DCC6` **لحد يوم الخميس · اطلب دلوقتي**. End side: 76 px orange circle with the bowl icon.
3. **الأقسام** — `SectionHeader` with **عرض الكل** → `/categories/all`. Grid 3 columns, gap 10: tile = white card, 54 px tinted circle + icon 28 px, name 13/700 centered. Tap → `/categories/:slug`.
4. **عروض النهاردة** — horizontal scroll row of discounted `ProductCard` (width 156), bleeding to the screen edges; header link → `/offers`.
5. **الأكثر طلباً** — 2-column grid of `ProductCard` (`is_featured` products).
6. `BottomNav`.

**ProductCard (round-add)**: white card, padding 8, gap 8. Thumb height 96 radius 12 (discount badge top-start). Name 15/700, unit 12 `muted` (e.g. ربع كيلو). Bottom row: price column (price 16/800 + old price struck through 12 `muted`) on the start; on the end a **44 px orange circle "+" button** (`aria-label="أضف {name} للسلة"`) that adds the default variant ×1 and shows a toast. Tapping image/name → product page.

### 6.2 Category `/categories/:slug`
- `TopBar`: back → `/`, title = category name (or **كل المنتجات**), end action: 44 px search icon button.
- `ChipRow` (padding 12/16): **الكل**, then every category. Selecting updates the URL.
- Caption 13/600 `muted`: **{n} منتج**.
- 2-column grid of `ProductCard (stepper)`: same card, but under the price row a full-width control: if not in cart → **أضف للسلة** pill button (height 44, bg `primary`, plus icon); if in cart → full-width stepper (+ / qty / −). Qty 0 removes the line.
- When the cart is not empty a **sticky cart bar** sits above the bottom nav (margin 0 16 10, height 56, radius 16, bg `ink`, text `on-dark`): start = cart icon + **عرض السلة · {count} منتج**; end = total 17/800 in `primary`. Tap → `/cart`.
- Infinite scroll / "load more" for long lists.

### 6.3 Product `/products/:slug`
- Hero image area 280 px tall (category tint + 120 px icon when no image). **Back button**: 44 px white circle at the top-start corner (14 px inset). If the product has an active offer: red pill at the bottom-start of the hero, e.g. **عليه خصم 15%**.
- Body padding 18/16, gap 18:
  - Badges row: category (bg `primary-soft`, text `brand-deep`) + availability **متوفر** (success) or **خلصان** (danger soft).
  - Name h1 26/800; description 15/1.7 `ink-2`.
  - **اختار الوزن** (16/800): 3-column grid of variant buttons, min-height 64, radius 14, border 2px; each shows label 14/700 (ربع كيلو / نص كيلو / كيلو) and price 13 `muted`. Selected: border `primary`, bg `primary-tint`; else border `border`, bg white. `aria-pressed`.
  - Row: **الكمية** (16/800) on start, `QtyStepper` on end (min 1).
  - **ملاحظة للمحل (اختياري)** textarea, 2 rows, placeholder **مثلاً: عايزه مطحون ناعم** (saved on the cart line).
  - After adding: green box **اتضاف للسلة** with link **روح للسلة** on the end.
- **Fixed bottom bar** (white, top border, padding 12/16/18): start = **الإجمالي** caption + total 20/800 (variant price × qty); end (flex 1) = primary button with cart icon **أضف للسلة**. If unavailable: disabled button **المنتج خلصان حالياً**.

### 6.4 Offers `/offers`
- White header: h1 **العروض** on start, small logo (36 px) on end.
- Active offers rendered by type, stacked, gap 14:
  - **percentage** → dark banner (bg `ink`): pill **خصم**, title e.g. **15% على كل البهارات** 22/800, sub-text **ساري لحد الخميس 12 نوفمبر · الخصم بيتحسب لوحده في السلة** (date from `ends_at`), button **تسوّق البهارات** (height 44, bg `primary`, radius 12) → target category.
  - **bundle** → soft card (bg `primary-soft`): pill **باكدج** (white bg), name 20/800 (**باكدج الشتا**), items line (**ينسون + كركديه + عسل نحل ربع كيلو**), price 20/800 + old price struck; button on the end **أضف الباكدج** (primary, height 48) adds the bundle as one cart line.
  - **free_delivery** → success card (bg `#E3F1E1`): 48 px white circle with `truck` icon, **توصيل مجاني** 18/800, **على أي طلب فوق 500 ج.م**.
- Section **منتجات عليها خصم**: 2-column grid of discounted `ProductCard (round-add)`.

### 6.5 Cart `/cart`
- White header: **السلة** h1 on start, **{count} منتج** (14/700 `muted`) on end.
- Line item card (padding 10, gap 12): 72 px thumb · column (name 15/700; `{unit} · {unit price}` 12 `muted`; line total 15/800) · end column: stepper (+ / qty / −) and under it a small red text button with trash icon **شيل**.
- Free-delivery progress (success card): text **فاضلك {x} ج.م وتاخد توصيل مجاني** or **مبروك! طلبك عليه توصيل مجاني**; 8 px progress bar (white track, `success` fill).
- **عنوان التوصيل** textarea, placeholder **المنطقة، الشارع، رقم العمارة والدور** (required to checkout; prefilled from the customer's last address).
- Summary card rows: **المجموع** · **خصم ...** (red, one row per applied offer, label from the offer name) · **التوصيل** (value or **مجاني**) · divider · **الإجمالي** 18/800 · note **الدفع كاش عند الاستلام** (13 `muted`).
- Primary button **كمّل الطلب**: guest → `/account?next=checkout`; logged in → POST order → `/orders/:id/success`.
- Totals are previewed client-side but **always taken from `POST /cart/quote/`** (server is the source of truth for offers & delivery fee).
- Empty state: cart icon 48 `#B9A694`, **السلة فاضية**, link **ابدأ التسوق** → `/`.

### 6.6 Account `/account` (sign-up / login)
- `TopBar` title **حسابي**, back → previous page.
- Centered: 84 px logo circle, h2 **اعمل حسابك في ثانية** (22/800), sub-text **محتاجين اسمك ورقم موبايلك بس عشان نوصلّك طلبك**.
- Fields (padding 24/20, gap 18):
  - **الاسم** — required, min 2 chars, placeholder **مثلاً: محمد أحمد**, `autocomplete="name"`.
  - **رقم الموبايل** — required, `type="tel"`, `inputmode="numeric"`, `dir="ltr"` text-aligned right, placeholder `01xxxxxxxxx`, Egyptian mobile regex `^01[0125][0-9]{8}$`. Normalize Arabic-Indic digits to Western before validating.
  - **الإيميل (اختياري)** — "(اختياري)" in 600 `muted`, `type="email"`, `dir="ltr"`, placeholder `name@example.com`.
- Primary button **إنشاء الحساب وتأكيد الطلب** (when coming from checkout; otherwise **إنشاء الحساب**). Disabled style until valid, with hint under it: **اكتب اسمك ورقم موبايل صحيح (11 رقم يبدأ بـ 01)**.
- Footer line: **عندك حساب؟ ادخل برقم موبايلك** → login mode: only the phone field + primary **دخول** (no OTP, no password). Footer in login mode: **مش عندك حساب؟ اعمل حساب جديد**.
- If register returns `phone_exists` → switch to login mode with the phone prefilled and the message **الرقم ده عنده حساب، ادخل بيه**. If login returns 404 → **مفيش حساب بالرقم ده** + switch to register mode.
- Logged-in view: name, phone, email, **طلباتي** list (order #, date, total, `StatusPill`), **تسجيل خروج** text button.

### 6.7 Order success `/orders/:id/success`
Centered column (padding 40/20/20, gap 16): 104 px circle `#E3F1E1` with a 56 px green check · h1 **طلبك وصل لأبو سمرة!** · pill **رقم الطلب #{number}** (bg `primary-soft`, text `brand-deep`) · paragraph **هنكلمك على رقمك خلال دقايق نأكد الطلب ونقولك ميعاد التوصيل.** · summary card (**عدد المنتجات**, **الإجمالي**, **طريقة الدفع: كاش عند الاستلام**) · primary button **كمّل تسوق** → `/` · link with phone icon **اتصل بالمحل** (`tel:` from `/settings/`). Bottom nav visible, active حسابي.

## 7. Admin screens

All admin screens: `AdminHeader` + scrollable content (padding 16) + admin `BottomNav`. Header end-side action defaults to **شوف المتجر** (eye icon, bg `primary-tint`, text `brand-deep`, height 44, radius 12) → opens `/` in a new tab.

### 7.1 Dashboard `/admin`
- h1 **أهلاً يا أبو سمرة**, caption **{weekday date} · ملخص النهاردة**.
- Stats grid 2×2 (cards: 36 px icon square bg `primary-tint`, label 13/600 `ink-2`, value 24/800): **طلبات النهاردة** · **مبيعات النهاردة** · **مستنية تأكيد** (highlighted: bg `primary-soft`, border `primary`) · **زبائن جدد الأسبوع ده**.
- 2 quick buttons (grid 2): **إضافة منتج** (primary, plus icon) → product form; **عرض جديد** (bg `ink`, text `on-dark`, tag icon) → `/admin/offers`.
- **طلبات جديدة محتاجة تأكيد** + link **كل الطلبات**: up to 3 cards: `#{number} · {name}` 800 + time ago (12 `muted`) on the end; items summary 14 `ink-2`; bottom row: total 17/800 on start, on end a 44 px call button (`tel:`) and **تأكيد الطلب** (primary, height 44) → sets status `preparing`; then it becomes a green **اتأكد** label.
- **قرب يخلص من المخزن** + link **المنتجات**: card list rows (min-height 52): name 700 on start, red **باقي {x}** on end (products with `stock_qty <= low_stock_threshold`).
- Auto-refresh every 30 s while visible; new-order count badge on the الطلبات nav item.

### 7.2 Orders `/admin/orders`
- Status chips: **جديد (n)** · **بيتجهز (n)** · **في الطريق (n)** · **اتسلم (n)** (+ **اتلغى** in an overflow menu).
- Order card (padding 14, gap 8): row `طلب #{number}` 16/800 + `StatusPill` · row name 700 + phone (`dir="ltr"`) · items line · `{area} · {time}` 13 `muted` · divider · row total 18/800 on start; on end **اتصال** (phone icon, bg `primary-tint`, `tel:`) and the next-step primary button:
  - new → **ابدأ التجهيز**, preparing → **خرج للتوصيل**, out_for_delivery → **اتسلم**, delivered → none.
- Tapping the card opens a bottom sheet with full details (lines with variants & notes, address, applied discounts) and **إلغاء الطلب** (danger, with confirm).
- Empty: **مفيش طلبات هنا**.

### 7.3 Products `/admin/products`
- Header end action: **منتج جديد** (primary, plus icon, height 44).
- Search field (border `input-border`, placeholder **ابحث باسم المنتج**), category chips (height 40).
- Row card: 56 px thumb · name 15/700 + `{unit} · {price}` · `ToggleSwitch` **متوفر / خلصان** (PATCH `is_available` instantly, optimistic) · 44 px edit button (pencil, bg `primary-tint`) → form.

### 7.4 Product form `/admin/products/new|:id`
- `TopBar` **إضافة منتج** / **تعديل منتج**, back → list.
- Image upload box: height 150, 2px dashed `dashed`, bg `primary-tint`, image icon 36, **اضغط لإضافة صورة المنتج** (compress client-side to ≤ 1200 px, webp).
- **اسم المنتج** (placeholder **مثلاً: كمون مطحون**), **القسم** (select).
- **الأسعار حسب الوزن**: column captions **الوزن** / **السعر (ج.م)**; each row = text input + number input + 44 px red delete button (bg `#FDE7E5`); dashed button **إضافة وزن**. At least one variant required; first variant = default.
- **وصف قصير** textarea, placeholder **اكتب سطرين عن المنتج واستخداماته**.
- Settings card with switches: **متاح للبيع**, **يظهر في "الأكثر طلباً"**. (Optional fields: stock qty, low-stock threshold.)
- Fixed bottom bar: **حفظ المنتج** (primary, flex 2) and **إلغاء** (bg `primary-tint`, text `brand-deep`, flex 1). Edit mode adds a **حذف المنتج** danger text button at the bottom of the form.

### 7.5 Offers `/admin/offers`
- Card **عرض جديد**:
  - Segmented control (bg `primary-tint`, padding 4, radius 14; selected segment bg `primary`): **خصم %** · **باكدج** · **توصيل مجاني**.
  - **اسم العرض** (placeholder changes per type: **مثلاً: خصم البهارات** / **مثلاً: باكدج رمضان** / **مثلاً: توصيل مجاني للطلبات الكبيرة**).
  - percentage: **نسبة الخصم %** + **على** (select: a category / specific products / **كل المتجر**).
  - bundle: **المنتجات اللي في الباكدج** (multi-select of variants with qty) + **سعر الباكدج (ج.م)**.
  - free_delivery: **أقل قيمة للطلب (ج.م)**.
  - **يبدأ من** / **ينتهي في** (date inputs, 2 columns; end optional), checkbox "يظهر كعرض الأسبوع في الرئيسية".
  - Primary **نشر العرض**.
- **العروض الحالية**: cards with type pill, title 15/800, validity caption, `ToggleSwitch` **شغّال / واقف** on the end; tap card to edit.

### 7.6 Customers `/admin/customers`
- Search **ابحث بالاسم أو رقم الموبايل**, caption **مرتبين حسب آخر طلب**.
- Row card: 48 px initial avatar (bg `primary-soft`, text `brand-deep`, 18/800) · name 15/800, phone (`dir="ltr"`), email or **بدون إيميل**, line **{n} طلب · {spent} · آخر طلب {when}** · 44 px call button on the end. Tap → customer's orders.

## 8. State & business rules

- **Cart** (Pinia, persisted): lines `{variantId, productId, name, unitLabel, unitPrice, qty, note, bundleOfferId?}`. Badge count = sum of qty. Cart survives offline and reloads; prices re-validated with `/cart/quote/` on cart open and before checkout (show a notice if something changed or became unavailable).
- **Offers** (computed server-side, previewed client-side): `percentage` on category/products/all; `bundle` fixed price; `free_delivery` above a threshold. Delivery fee and free-delivery threshold come from `/settings/`. Rounding: whole pounds.
- **Auth**: JWT (access in memory + refresh in persisted store). Customers: register with name + phone (+ optional email), login with phone only — no OTP, no password. Admin: staff user, phone + password login. 401 → refresh once → else logout.
- Order statuses: `new → preparing → out_for_delivery → delivered`, or `cancelled`. Payment: `cod` only for now.
- Order numbers shown as `#1048` (server `number` field).

## 9. API contract (DRF, base `/api/v1/`, JSON, Arabic `detail` messages)

Public:
- `GET /settings/` → `{shop_name, phone, whatsapp, delivery_fee, free_delivery_threshold, currency:"EGP"}`
- `GET /categories/` → `[{id, slug, name, color, icon, order}]`
- `GET /products/?category=&q=&featured=&discounted=&page=` → paginated `{count, next, results:[Product]}`
- `GET /products/{slug}/` → `Product`
  `Product = {id, slug, name, description, category:{slug,name,color,icon}, image, is_available, is_featured, variants:[{id, label, price, old_price|null, is_default}], active_offer:{id,name,type,value}|null}`
- `GET /offers/active/` → `[{id, type:"percentage"|"bundle"|"free_delivery", name, description, value, target:{kind:"category"|"products"|"all", ids|slug}, bundle_items:[{variant_id, name, qty}], bundle_price, old_price, min_order, starts_at, ends_at, is_featured}]`
- `POST /cart/quote/` `{items:[{variant_id, qty}], bundles:[{offer_id, qty}]}` → `{lines:[...], subtotal, discounts:[{offer_id, label, amount}], delivery_fee, free_delivery_threshold, free_delivery_remaining, total, warnings:[{variant_id, code, detail}]}` (use `free_delivery_remaining` for the progress bar)

Auth:
- `POST /auth/register/` `{name, phone, email?}` → 201 `{access, refresh, user}` · 409 `{detail, code:"phone_exists"}`
- `POST /auth/login/` `{phone}` → 200 `{access, refresh, user}` · 404 `{detail, code:"not_found"}` (customers only)
- `POST /auth/admin/login/` `{phone, password}` → `{access, refresh, user}` (staff only) · `POST /auth/token/refresh/` `{refresh}`
- `POST /auth/logout/` `{refresh}` → 204
- `GET/PATCH /me/` → `{id, name, phone, email, default_address, area, is_staff}`

Customer orders:
- `POST /orders/` `{items, bundles, address, area?, notes?}` → 201 `Order` (server recomputes totals) · 409 `{detail, code:"cart_changed", quote}` → show the fresh quote and ask the customer to review the cart
- `GET /orders/mine/` · `GET /orders/{id}/`
  `Order = {id, number, status, created_at, customer:{name, phone}, address, area, lines:[{name, unit_label, qty, unit_price, line_total, note}], subtotal, discounts, delivery_fee, total, payment_method:"cod"}`

Admin (`IsAdminUser`):
- `GET /admin/dashboard/` → `{orders_today, sales_today, pending_count, new_customers_week, low_stock:[{id,name,stock_qty,stock_unit}]}`
- `GET /admin/orders/?status=` · `PATCH /admin/orders/{id}/` `{status}` · `GET /admin/orders/counts/` → `{new, preparing, out_for_delivery, delivered, cancelled}`
- `GET/POST /admin/products/` · `GET/PATCH/DELETE /admin/products/{id}/` (multipart for image; variants nested)
- `GET/POST /admin/offers/` · `PATCH/DELETE /admin/offers/{id}/`
- `GET /admin/customers/?q=` → `[{id, name, phone, email, orders_count, total_spent, last_order_at}]`

Errors: `{detail}` or field errors `{field:[msg]}` — map field errors onto the matching form inputs.

## 10. PWA

- Manifest: `name: "أبو سمرة – عطارة وبهارات"`, `short_name: "أبو سمرة"`, `lang: "ar"`, `dir: "rtl"`, `start_url: "/"`, `scope: "/"`, `display: "standalone"`, `orientation: "portrait"`, `theme_color: "#F7A04B"`, `background_color: "#FFF8F1"`, icons 192/512/maskable 512, shortcuts: **العروض** (`/offers`), **السلة** (`/cart`).
- `<meta name="theme-color" content="#F7A04B">`, apple-touch-icon, iOS status bar style.
- Workbox runtime caching:
  - App shell + fonts + icons: precache.
  - `GET /categories/`, `/products*`, `/offers/active/`, `/settings/`: **StaleWhileRevalidate** (max 24 h).
  - Product images: **CacheFirst** (max 200 entries, 30 days).
  - Auth, cart quote, orders, all `/admin/*`: **NetworkOnly**.
- Offline: browsing cached catalog works; a slim banner at the top **انت أوفلاين دلوقتي — هتقدر تتفرج بس الطلب محتاج نت**; the checkout button is disabled while offline.
- Install: custom prompt card on Home after the 2nd visit (**نزّل تطبيق أبو سمرة على موبايلك** + **تثبيت** / **مش دلوقتي**), iOS instructions sheet for Safari.
- Update: when a new SW is waiting, show a toast **فيه نسخة جديدة** with **تحديث**.

## 11. Project structure

```
src/
  api/          client.ts, catalog.ts, cart.ts, orders.ts, auth.ts, admin/*.ts
  stores/       cart.ts, auth.ts, settings.ts, catalog.ts
  components/   ui/ (Button, Input, Chip, ToggleSwitch, QtyStepper, StatusPill, Toast…), store/, admin/
  layouts/      StoreLayout.vue, AdminLayout.vue
  views/store/  Home, Category, Product, Offers, Cart, Account, OrderSuccess
  views/admin/  Login, Dashboard, Orders, Products, ProductForm, Offers, Customers
  composables/  useMoney, usePhone, useOnline, useInstallPrompt
  router/       index.ts (guards: auth, staff)
  styles/       main.css (Tailwind + font imports)
```
`.env`: `VITE_API_BASE_URL`. Add a `msw` mock layer with sample data (the 16 products and 6 categories from the design) so the UI runs before the backend is ready.

## 12. Acceptance checklist

- [ ] Every screen above matches the layout, copy and colors at 390 px; nothing overflows at 360 px.
- [ ] Full flow works: browse → add (card, stepper, product page with weight) → cart → sign up → order → success.
- [ ] Offers reflect in cart totals from `/cart/quote/`; free-delivery progress updates live.
- [ ] Phone validation accepts `01012345678`, rejects `0101234567` and `02…`; Arabic digits are normalized.
- [ ] Admin: confirm/advance order status, toggle availability, create product with 3 weights, create & pause an offer.
- [ ] Lighthouse: PWA installable, Accessibility ≥ 95, Performance ≥ 90 on mobile.
- [ ] Works offline for browsing; checkout blocked with the offline message.
- [ ] Keyboard and screen-reader labels on all icon buttons; focus ring visible.

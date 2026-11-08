# Build Prompt — "أبو سمرة" Spice Shop Store (Django REST Framework backend)

Build the **backend API** for **أبو سمرة (Abo Samra)**, a traditional Egyptian spice & herb shop (عطارة) in Cairo. The frontend is a separate **Vue 3 PWA** that already expects the API contract in Section 6 — match it exactly (paths, field names, status codes).

> **Use my DRF skill file for project layout, conventions, settings structure, Docker, CI and code style.** This prompt only defines the domain: models, business rules, endpoints, permissions and tests. Where the two conflict on *conventions*, the skill wins; where they conflict on *the contract or business rules*, this prompt wins.

Scope: customers browse a catalog, see offers, build a cart, register with **name + phone (email optional)**, and place **cash-on-delivery** orders. The shop owner manages orders, products, offers and customers from an admin dashboard.

---

## 1. Stack

- Python 3.12, Django 5.x, Django REST Framework
- PostgreSQL
- `djangorestframework-simplejwt` (with token rotation + blacklist)
- `django-filter`, `drf-spectacular` (OpenAPI at `/api/schema/`, Swagger at `/api/docs/`)
- `django-cors-headers` (allow the Vue origin from env)
- `Pillow` for image processing; media storage via `django-storages` (S3-compatible) in prod, local in dev
- `pytest` + `pytest-django` + `factory_boy`

Settings: `LANGUAGE_CODE = "ar"`, `TIME_ZONE = "Africa/Cairo"`, `USE_TZ = True`. All money is `DecimalField(max_digits=10, decimal_places=2)` and returned as JSON numbers rounded to whole pounds (no decimals shown in the UI). All user-facing error messages are in Egyptian Arabic.

## 2. Apps

`core` (shop settings, utilities) · `accounts` (custom user, auth) · `catalog` (categories, products, variants) · `offers` (offers, bundle items) · `orders` (orders, lines, discounts, status log, pricing engine).

## 3. Models

### accounts.User (custom, set `AUTH_USER_MODEL` before the first migration)
- `phone` — `CharField(11, unique=True)`, **`USERNAME_FIELD`**, always stored normalized (see 4.1)
- `name` — `CharField(80)`
- `email` — `EmailField(blank=True)`
- `default_address` — `TextField(blank=True)`; `area` — `CharField(80, blank=True)`
- `is_staff`, `is_active`, `date_joined`
- Customers have an **unusable password**. Staff users have a real password.
- Custom manager: `create_user(phone, name, email="")`, `create_superuser(phone, name, password)`.

### core.ShopSettings (singleton — `pk=1`, get-or-create helper, editable in Django admin)
`shop_name` ("أبو سمرة") · `phone` · `whatsapp` · `delivery_fee` (default 30) · `free_delivery_threshold` (default 500) · `is_accepting_orders` (bool, default True).

### catalog
- **Category**: `slug` (unique, ASCII: `spices`, `herbs`, `honey`, `nuts`, `grains`, `incense`), `name`, `color` (hex), `icon` (lucide icon name), `order`, `is_active`.
- **Product**: `category` FK, `name`, `slug` (unique, `allow_unicode=True`, auto from name + short suffix on clash), `description`, `image` (optional), `is_available` (default True), `is_featured`, `stock_qty` (Decimal, nullable → null means "not tracked"), `low_stock_threshold` (Decimal, nullable), `stock_unit` (e.g. "كيلو"), `created_at`, `updated_at`.
  - On image upload: resize to max 1200 px longest side, convert to WebP, strip EXIF.
- **ProductVariant**: `product` FK (related_name `variants`), `label` ("ربع كيلو" / "نص كيلو" / "كيلو" / "لتر" / "علبة"), `price`, `compare_at_price` (nullable — manual "old price" shown struck-through), `stock_factor` (Decimal, how much of `stock_qty` one unit consumes, e.g. 0.25 for ربع كيلو; default 1), `is_default`, `order`.
  - Constraint: exactly one default variant per product (enforce in serializer + `UniqueConstraint(condition=Q(is_default=True))`).

### offers
- **Offer**: `type` (`percentage` | `bundle` | `free_delivery`), `name`, `description`, `value` (percent, for `percentage`), `target_kind` (`category` | `products` | `all`), `target_category` FK nullable, `target_products` M2M Product, `bundle_price` (nullable), `min_order` (nullable, for `free_delivery`), `starts_at` (default now), `ends_at` (nullable = no end), `is_active` (owner's on/off switch), `is_featured` (shown as "عرض الأسبوع" on home), `created_at`.
  - Manager method `Offer.objects.live(now)` → `is_active=True, starts_at <= now, (ends_at is null or ends_at > now)`.
  - Validation per type: percentage needs `value` 1–90 and a valid target; bundle needs ≥ 2 bundle items and `bundle_price`; free_delivery needs `min_order`.
- **BundleItem**: `offer` FK (related_name `bundle_items`), `variant` FK, `qty` (≥ 1).

### orders
- **Order**: `number` (unique int, sequential starting at **1001**, generated inside the create transaction — use a Postgres sequence), `customer` FK User (PROTECT), `status` (`new` | `preparing` | `out_for_delivery` | `delivered` | `cancelled`, default `new`), `address`, `area`, `notes`, `subtotal`, `discount_total`, `delivery_fee`, `total`, `payment_method` (`cod` only), `created_at`, `updated_at`.
- **OrderLine**: `order` FK (related_name `lines`), `variant` FK nullable (SET_NULL), `bundle_offer` FK nullable (SET_NULL), **snapshots**: `name`, `unit_label`, `unit_price`, `qty`, `line_total`, `note`.
- **OrderDiscount**: `order` FK, `offer` FK nullable (SET_NULL), `label` (snapshot of offer name), `amount`.
- **OrderStatusLog**: `order` FK, `from_status`, `to_status`, `changed_by` FK nullable, `created_at`.

Indexes: `Order(status, created_at)`, `Order(customer, created_at)`, `Product(category, is_available)`, `User(phone)`.

## 4. Business rules

### 4.1 Phone normalization (one utility, used everywhere — register, login, admin search, admin create)
1. Convert Arabic-Indic (`٠١٢٣٤٥٦٧٨٩`) and Persian digits to Western.
2. Strip spaces, dashes, parentheses.
3. `+20XXXXXXXXXX` / `0020…` / `20XXXXXXXXXX` → `0XXXXXXXXXX`.
4. Must match `^01[0125][0-9]{8}$`, else 400 `{"phone": ["اكتب رقم موبايل مصري صحيح (11 رقم يبدأ بـ 01)"]}`.

### 4.2 Authentication — **no OTP, no customer passwords**
- **Register** `{name, phone, email?}`: name 2–80 chars; email optional but validated if sent. If the phone already exists → **409** `{"detail": "الرقم ده عنده حساب، ادخل بيه", "code": "phone_exists"}`. Success → **201** with JWT pair + user.
- **Login (customer)** `{phone}`: if an active, non-staff user exists → **200** JWT pair + user; otherwise **404** `{"detail": "مفيش حساب بالرقم ده", "code": "not_found"}`. Staff accounts can't log in through this endpoint (return the same 404).
- **Admin login** `{phone, password}`: staff only; wrong credentials → 401 `{"detail": "الرقم أو الباسورد غلط"}`.
- JWT: access 30 min; refresh **60 days** for customers, 7 days for staff; `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True`. Add claims `name`, `is_staff`.
- Throttling (scoped): `auth` = 10/min per IP on register + both logins; `quote` = 60/min; `orders` = 10/min per user.
- Because customer login is phone-only, a logged-in customer can only ever reach **their own** profile and orders — never other customers' data. Keep customer tokens minimal-privilege.

### 4.3 Pricing engine — `orders/services/pricing.py`
One pure function used by **both** `/cart/quote/` and order creation:

```python
quote(items: list[{variant_id, qty}], bundles: list[{offer_id, qty}], now=None) -> Quote
```

1. **Load & validate lines.** qty is an int 1–50. Unknown variant, product unavailable, inactive category or not enough tracked stock → drop the line and add a warning `{variant_id, code: "unavailable"|"not_found"|"insufficient_stock", detail}`. (Order creation turns warnings into an error — see 4.4.)
2. **Regular lines:** `line_total = variant.price × qty`. (`compare_at_price` is display-only, never used in math.)
3. **Bundles:** each live bundle offer becomes one line `name = offer.name`, `unit_price = bundle_price`, `line_total = bundle_price × qty`. Its items' stock is checked like regular lines. Expired/inactive bundle → warning `offer_expired`.
4. `subtotal` = sum of all line totals.
5. **Percentage offers** (live only): for each regular line find every percentage offer whose target matches (`all`, the product's category, or the product in `target_products`). If several match one line, apply **only the highest percentage** (no stacking). Bundle lines never get percentage discounts. Group the discount per offer → `discounts: [{offer_id, label: offer.name, amount}]`, each amount rounded to whole pounds (round half up). `discount_total` = sum.
6. **Delivery:** `threshold = min(settings.free_delivery_threshold, min_order of any live free_delivery offer)`. `after_discount = subtotal − discount_total`. If `after_discount >= threshold` → `delivery_fee = 0`, else `settings.delivery_fee`. `free_delivery_remaining = max(0, threshold − after_discount)`.
7. `total = subtotal − discount_total + delivery_fee`.

Return `{lines:[{variant_id|null, offer_id|null, name, unit_label, qty, unit_price, line_total}], subtotal, discounts, discount_total, delivery_fee, free_delivery_threshold, free_delivery_remaining, total, warnings}`.

**Reference case (must be a test):** spices offer 15% live, delivery fee 30, threshold 500.
Cart: كمون مطحون ربع كيلو (60) ×2, فلفل أسود حب ربع كيلو (95) ×1, عسل نحل طبيعي كيلو (220) ×1
→ subtotal **435**, discount **32** (15% of 215 = 32.25 → 32), delivery **30**, total **433**, free_delivery_remaining **97**.

### 4.4 Order creation (`POST /orders/`)
- Requires auth and `ShopSettings.is_accepting_orders` (else 503 `{"detail": "المحل مش بياخد طلبات دلوقتي"}`).
- Body `{items, bundles, address (required, min 10 chars), area?, notes?}`.
- In one `transaction.atomic()`: lock tracked products with `select_for_update`, run `quote()`. If there are **any** warnings or no lines → **409** `{"detail": "فيه حاجات في السلة اتغيرت", "code": "cart_changed", "quote": <fresh quote>}`.
- Snapshot lines and discounts, generate `number`, decrement `stock_qty` by `qty × stock_factor` for tracked products (bundle items included), write the first `OrderStatusLog` (`null → new`).
- Save `address`/`area` back to `user.default_address`/`area`.
- After commit: send a notification hook for the new order (a `notify_new_order(order)` function — log-only stub for now, so WhatsApp/push can be plugged in later).

### 4.5 Order status
Allowed transitions (admin only):
`new → preparing | cancelled` · `preparing → out_for_delivery | cancelled` · `out_for_delivery → delivered | cancelled` · `delivered` and `cancelled` are final.
Invalid → 400 `{"detail": "مينفعش تغيّر الحالة من {from} لـ {to}"}`. Every change writes `OrderStatusLog`. Cancelling **restores tracked stock**.

### 4.6 Catalog visibility
Public endpoints only return active categories and products in active categories. Unavailable products **are listed** (with `is_available: false`, so the UI shows "خلصان") but can't be ordered.

## 5. Serializers — response shapes (field names are part of the contract)

```text
Category  = {id, slug, name, color, icon, order}
Variant   = {id, label, price, old_price (= compare_at_price | null), is_default}
Product   = {id, slug, name, description, image (absolute URL | null), is_available, is_featured,
             category: {slug, name, color, icon},
             variants: [Variant],               # ordered, default first
             active_offer: {id, name, type, value} | null}   # best live percentage offer for this product
Offer     = {id, type, name, description, value, target: {kind, slug|null, ids: []},
             bundle_items: [{variant_id, name, qty}], bundle_price, old_price (sum of bundle items' prices),
             min_order, starts_at, ends_at, is_featured}
User      = {id, name, phone, email, default_address, area, is_staff}
Order     = {id, number, status, created_at, customer: {name, phone}, address, area, notes,
             lines: [{name, unit_label, qty, unit_price, line_total, note}],
             subtotal, discounts: [{offer_id, label, amount}], discount_total, delivery_fee, total,
             payment_method}
```

Error format: `{"detail": "...", "code": "..."}` for general errors, `{"field": ["..."]}` for validation errors (DRF default), messages in Arabic.

Pagination: `PageNumberPagination`, `page_size=20`, `?page=` → `{count, next, previous, results}`.

## 6. Endpoints (base `/api/v1/`)

### Public (AllowAny)
| Method & path | Notes |
|---|---|
| `GET /settings/` | `{shop_name, phone, whatsapp, delivery_fee, free_delivery_threshold, currency: "EGP", is_accepting_orders}` |
| `GET /categories/` | not paginated, ordered by `order` |
| `GET /products/` | filters: `category` (slug, `all` = no filter), `q` (icontains name/description), `featured=true`, `discounted=true` (has `compare_at_price` on any variant **or** a live percentage offer applies). Paginated. `prefetch_related("variants")`, `select_related("category")` — no N+1. |
| `GET /products/{slug}/` | |
| `GET /offers/active/` | live offers; featured first |
| `POST /cart/quote/` | `{items, bundles}` → quote (4.3). Also works for guests. |

### Auth
| Method & path | Notes |
|---|---|
| `POST /auth/register/` | 201 `{access, refresh, user}` / 409 `phone_exists` |
| `POST /auth/login/` | `{phone}` → 200 / 404 `not_found` |
| `POST /auth/admin/login/` | `{phone, password}`, staff only |
| `POST /auth/token/refresh/` | `{refresh}` → `{access, refresh}` |
| `POST /auth/logout/` | `{refresh}` → blacklist, 204 |
| `GET / PATCH /me/` | update `name`, `email`, `default_address`, `area` (phone not editable) |

### Customer (IsAuthenticated)
| Method & path | Notes |
|---|---|
| `POST /orders/` | 4.4 |
| `GET /orders/mine/` | own orders, newest first, paginated |
| `GET /orders/{id}/` | own order only (404 otherwise) |

### Admin (IsAdminUser) — prefix `/admin/` (API, not Django admin)
| Method & path | Notes |
|---|---|
| `GET /admin/dashboard/` | `{orders_today, sales_today (sum of totals of today's non-cancelled orders), pending_count (status=new), new_customers_week (last 7 days), low_stock: [{id, name, stock_qty, stock_unit}]}` — "today" in Africa/Cairo |
| `GET /admin/orders/` | `?status=`, `?q=` (number, name, phone), newest first. Include `customer.phone` and a short `items_summary` ("كمون مطحون ×2، فلفل أسود، عسل نحل") |
| `GET /admin/orders/counts/` | `{new, preparing, out_for_delivery, delivered, cancelled}` |
| `GET /admin/orders/{id}/` · `PATCH /admin/orders/{id}/` | PATCH accepts `{status}` only (4.5) |
| `GET / POST /admin/products/` | multipart; nested `variants` (create/update/delete in one request, replace-by-id semantics); filters `category`, `q`, `is_available` |
| `GET / PATCH / DELETE /admin/products/{id}/` | DELETE = soft delete if the product has order lines (set `is_available=False` and hide from catalog via `is_archived`), hard delete otherwise |
| `GET / POST /admin/offers/` · `GET / PATCH / DELETE /admin/offers/{id}/` | nested `bundle_items`; PATCH `{is_active}` is the on/off switch |
| `GET /admin/customers/` | `?q=` name/phone (normalize phone input); annotated `orders_count`, `total_spent` (non-cancelled), `last_order_at`; ordered by `last_order_at` desc nulls last |
| `GET /admin/customers/{id}/orders/` | that customer's orders |

Also register every model in **Django admin** (Arabic verbose names) as a fallback back-office.

## 7. Seed data — `python manage.py seed_abo_samra`
Idempotent. Creates:
- ShopSettings (delivery 30, threshold 500).
- Categories (slug · name · color · icon): spices · بهارات · `#F6D9B8` · soup — herbs · أعشاب ومشروبات · `#DCEBCF` · leaf — honey · عسل وزيوت · `#F9E4A8` · droplet — nuts · مكسرات · `#EBD7C3` · nut — grains · بقوليات وحبوب · `#F2E6C9` · wheat — incense · بخور · `#E6DAEE` · flame.
- Products (default variant · price · compare_at): كمون مطحون ربع كيلو 60 (+ نص كيلو 115, كيلو 220) · فلفل أسود حب ربع 95 (110) · كركم ربع 45 · قرفة عيدان ربع 70 · بهارات مشكلة ربع 55 (65) · ينسون ربع 50 · كركديه ربع 65 · بابونج ربع 40 · حبة البركة ربع 55 · عسل نحل طبيعي كيلو 220 (250) · زيت زيتون لتر 280 · لوز مقشر ربع 120 · كاجو محمص ربع 150 (170) · عدس أصفر كيلو 60 · فريك كيلو 75 · بخور عود علبة 90. Featured: كمون، عسل، كركديه، لوز.
- Offers: "خصم 15% على كل البهارات" (percentage 15, category spices, ends next Thursday 23:59, featured) · "باكدج الشتا" (bundle: ينسون ربع + كركديه ربع + عسل ربع كيلو → 290) · "توصيل مجاني" (free_delivery, min_order 500).
- A staff user from env `ADMIN_PHONE` / `ADMIN_PASSWORD` / `ADMIN_NAME`.
These are placeholder prices — the owner will edit them.

## 8. Tests (pytest, must pass)
- Phone normalization: `٠١٠١٢٣٤٥٦٧٨` → `01012345678`; `+201012345678` → `01012345678`; rejects `0101234567`, `02123456789`.
- Register → 201; same phone again → 409 `phone_exists`; login with unknown phone → 404; staff phone on customer login → 404; admin login works only with the password.
- Pricing: the reference case in 4.3; best-percentage-wins (no stacking); bundles excluded from percentage; free delivery exactly at threshold; expired offers ignored; unavailable product → warning.
- Order create: totals equal the quote; 409 `cart_changed` when a product became unavailable; stock decremented with `stock_factor`; number sequence increments from 1001; address saved to profile.
- Status: valid chain works and logs; invalid jump → 400; cancel restores stock.
- Permissions: customer can't read another customer's order (404) or any `/admin/` endpoint (403); anonymous can quote but can't order (401).
- Query counts: `/products/` list is ≤ 4 queries regardless of page size.

## 9. Done when
- `docker compose up` + `migrate` + `seed_abo_samra` gives a working API the Vue app can use immediately.
- OpenAPI schema at `/api/schema/` matches Section 6 (generate and commit `openapi.yaml`).
- All tests in Section 8 pass; no N+1 on list endpoints.
- CORS allows only the configured frontend origin(s); `DEBUG=False` settings are production-safe per my DRF skill.

"""QA-05: end-to-end API journeys (BSPEC section 8) through DRF's APIClient.

PA_CHECKLIST rows verified: B2.1, B2.2, B2.3, B3.1, B4.1, B4.2, B4.7, B5.1, B5.2, B5.3, B6.1,
B7.1, B8.1, A1.1, A2.1, A5.1 (see the docstring of each test).
"""

from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Product, ProductVariant
from apps.catalog.tests.factories import CategoryFactory, make_product
from apps.offers.tests.factories import percentage_offer
from apps.orders.models import Order, OrderStatusLog

pytestmark = pytest.mark.django_db

ADDRESS = "12 شارع التحرير، الدقي"


def bearer(client, access):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


@pytest.fixture
def reference_shop():
    spices = CategoryFactory(slug="spices")
    honey = CategoryFactory(slug="honey")
    cumin_p, cumin = make_product(
        "كمون مطحون", 60, spices, stock_qty=Decimal("10"), stock_unit="كيلو"
    )
    cumin.stock_factor = Decimal("0.25")
    cumin.save()
    _, pepper = make_product("فلفل أسود حب", 95, spices)
    honey_p, honey_v = make_product(
        "عسل نحل طبيعي", 220, honey, label="كيلو", stock_qty=Decimal("5"), stock_unit="كيلو"
    )
    percentage_offer(15, category=spices, name="خصم 15% على كل البهارات")
    return {
        "cumin": cumin,
        "pepper": pepper,
        "honey": honey_v,
        "cumin_p": cumin_p,
        "honey_p": honey_p,
    }


def reference_items(shop):
    return [
        {"variant_id": shop["cumin"].id, "qty": 2, "note": "ناعم"},
        {"variant_id": shop["pepper"].id, "qty": 1},
        {"variant_id": shop["honey"].id, "qty": 1},
    ]


def test_full_customer_journey_register_quote_order_mine_detail(reference_shop):
    """B2.1, B3.1, B4.1, B4.2, B4.7, B7.1: register, quote, order, mine, detail."""
    shop = reference_shop
    client = APIClient()

    # Guests can browse and quote.
    assert client.get("/api/v1/settings/").status_code == 200
    cats = client.get("/api/v1/categories/").json()
    assert {c["slug"] for c in cats} >= {"spices", "honey"}
    listing = client.get("/api/v1/products/", {"category": "spices"}).json()
    assert listing["count"] == 2
    slug = next(p["slug"] for p in listing["results"] if p["name"] == "كمون مطحون")
    assert client.get(f"/api/v1/products/{slug}/").json()["variants"][0]["price"] == 60

    items = reference_items(shop)
    quote = client.post("/api/v1/cart/quote/", {"items": items}, format="json").json()
    assert (quote["subtotal"], quote["discount_total"], quote["delivery_fee"], quote["total"]) == (
        435, 32, 30, 433,
    )  # fmt: skip
    assert quote["free_delivery_remaining"] == 97
    assert quote["warnings"] == []

    # Ordering requires an account.
    assert (
        client.post(
            "/api/v1/orders/", {"items": items, "address": ADDRESS}, format="json"
        ).status_code
        == 401
    )

    reg = client.post(
        "/api/v1/auth/register/",
        {"name": "محمد أحمد", "phone": "٠١٠١٢٣٤٥٦٧٨", "email": "m@example.com"},
        format="json",
    )
    assert reg.status_code == 201
    assert reg.json()["user"]["phone"] == "01012345678"
    bearer(client, reg.json()["access"])
    assert client.get("/api/v1/me/").json()["name"] == "محمد أحمد"

    r = client.post(
        "/api/v1/orders/",
        {"items": items, "address": ADDRESS, "area": "الدقي", "notes": "اتصل قبل ما توصل"},
        format="json",
    )
    assert r.status_code == 201, r.json()
    order = r.json()
    assert order["number"] == 1001 and order["status"] == "new" and order["payment_method"] == "cod"
    assert order["total"] == quote["total"] == 433
    assert (
        order["subtotal"] == 435 and order["discount_total"] == 32 and order["delivery_fee"] == 30
    )
    assert [(ln["name"], ln["qty"], ln["line_total"]) for ln in order["lines"]] == [
        ("كمون مطحون", 2, 120), ("فلفل أسود حب", 1, 95), ("عسل نحل طبيعي", 1, 220),
    ]  # fmt: skip

    # Stock: cumin 2 x 0.25 = 0.5, honey 1 x 1.
    shop["cumin_p"].refresh_from_db()
    shop["honey_p"].refresh_from_db()
    assert shop["cumin_p"].stock_qty == Decimal("9.5")
    assert shop["honey_p"].stock_qty == Decimal("4")

    # Address / area saved to the profile; first status log is null -> new.
    me = client.get("/api/v1/me/").json()
    assert me["default_address"] == ADDRESS and me["area"] == "الدقي"
    log = OrderStatusLog.objects.get(order_id=order["id"])
    assert (log.from_status, log.to_status) == (None, "new")

    mine = client.get("/api/v1/orders/mine/").json()
    assert mine["count"] == 1 and mine["results"][0]["number"] == 1001
    detail = client.get(f"/api/v1/orders/{order['id']}/").json()
    assert detail["id"] == order["id"] and detail["total"] == 433

    # Another customer cannot see it (404, not 403) and has an empty history.
    other = APIClient()
    tokens = other.post(
        "/api/v1/auth/register/", {"name": "سارة", "phone": "01212345678"}, format="json"
    ).json()
    bearer(other, tokens["access"])
    assert other.get(f"/api/v1/orders/{order['id']}/").status_code == 404
    assert other.get("/api/v1/orders/mine/").json()["count"] == 0


def test_login_is_phone_only_for_customers_and_password_for_staff(customer, staff):
    """B2.2, B2.3: customer login without password; staff via /auth/admin/login/ only."""
    client = APIClient()
    ok = client.post("/api/v1/auth/login/", {"phone": "+201012345678"}, format="json")
    assert ok.status_code == 200 and ok.json()["user"]["is_staff"] is False
    assert (
        client.post("/api/v1/auth/login/", {"phone": "01099999999"}, format="json").status_code
        == 404
    )
    assert (
        client.post("/api/v1/auth/login/", {"phone": staff.phone}, format="json").status_code == 404
    )
    bad = client.post(
        "/api/v1/auth/admin/login/", {"phone": staff.phone, "password": "x"}, format="json"
    )
    assert bad.status_code == 401 and bad.json()["code"]
    as_customer = client.post(
        "/api/v1/auth/admin/login/", {"phone": customer.phone, "password": "x"}, format="json"
    )
    assert as_customer.status_code == 401
    good = client.post(
        "/api/v1/auth/admin/login/",
        {"phone": staff.phone, "password": "s3cret-pass"},
        format="json",
    )
    assert good.status_code == 200 and good.json()["user"]["is_staff"] is True


def test_admin_chain_dashboard_customers_and_cancel_restores_stock(reference_shop, customer, staff):
    """B5.1-B5.3, A1.1, A2.1, A5.1: 2 orders; chain one, cancel the other."""
    shop = reference_shop
    cust = bearer(APIClient(), _access(customer))
    admin = bearer(APIClient(), _access(staff))
    items = reference_items(shop)

    first = cust.post("/api/v1/orders/", {"items": items, "address": ADDRESS}, format="json").json()
    second = cust.post(
        "/api/v1/orders/", {"items": items, "address": ADDRESS}, format="json"
    ).json()
    shop["cumin_p"].refresh_from_db()
    shop["honey_p"].refresh_from_db()
    assert shop["cumin_p"].stock_qty == Decimal("9.0") and shop["honey_p"].stock_qty == Decimal("3")

    dash = admin.get("/api/v1/admin/dashboard/").json()
    assert dash["orders_today"] == 2 and dash["sales_today"] == 866 and dash["pending_count"] == 2

    counts = admin.get("/api/v1/admin/orders/counts/").json()
    assert counts["new"] == 2
    listing = admin.get("/api/v1/admin/orders/", {"status": "new"}).json()
    assert [o["number"] for o in listing["results"]] == [1002, 1001]
    assert admin.get("/api/v1/admin/orders/", {"q": "٠١٠١٢٣٤٥٦٧٨"}).json()["count"] == 2

    url = f"/api/v1/admin/orders/{first['id']}/"
    skip = admin.patch(url, {"status": "delivered"}, format="json")
    assert skip.status_code == 400 and skip.json()["code"] == "invalid_transition"
    for status in ("preparing", "out_for_delivery", "delivered"):
        r = admin.patch(url, {"status": status}, format="json")
        assert r.status_code == 200 and r.json()["status"] == status
    assert cust.get(f"/api/v1/orders/{first['id']}/").json()["status"] == "delivered"
    assert OrderStatusLog.objects.filter(order_id=first["id"]).count() == 4
    assert admin.patch(url, {"status": "cancelled"}, format="json").status_code == 400

    # Delivered keeps stock; cancelling the second order restores exactly its share.
    shop["cumin_p"].refresh_from_db()
    assert shop["cumin_p"].stock_qty == Decimal("9.0")
    cancel = admin.patch(
        f"/api/v1/admin/orders/{second['id']}/", {"status": "cancelled"}, format="json"
    )
    assert cancel.status_code == 200
    shop["cumin_p"].refresh_from_db()
    shop["honey_p"].refresh_from_db()
    assert shop["cumin_p"].stock_qty == Decimal("9.5") and shop["honey_p"].stock_qty == Decimal("4")
    assert (
        admin.patch(
            f"/api/v1/admin/orders/{second['id']}/", {"status": "preparing"}, format="json"
        ).status_code
        == 400
    )
    assert OrderStatusLog.objects.filter(order_id=second["id"]).count() == 2

    # Customers screen: spend excludes the cancelled order.
    row = next(
        c for c in admin.get("/api/v1/admin/customers/", {"q": "0101"}).json()["results"]
        if c["phone"] == customer.phone
    )  # fmt: skip
    assert row["orders_count"] == 2 and row["total_spent"] == 433
    assert admin.get(f"/api/v1/admin/customers/{customer.id}/orders/").status_code == 200


def test_unavailable_product_is_listed_but_cannot_be_ordered(reference_shop, auth_client):
    """B6.1: availability toggled by admin is reflected publicly; ordering yields 409."""
    shop = reference_shop
    staff = User.objects.create_superuser(phone="01199999999", name="s", password="pw-123456")
    admin = bearer(APIClient(), _access(staff))
    pid = shop["pepper"].product_id
    assert (
        admin.patch(
            f"/api/v1/admin/products/{pid}/", {"is_available": False}, format="json"
        ).status_code
        == 200
    )
    public = APIClient().get("/api/v1/products/", {"category": "spices"}).json()["results"]
    pepper = next(p for p in public if p["id"] == pid)
    assert pepper["is_available"] is False
    r = auth_client.post(
        "/api/v1/orders/",
        {"items": [{"variant_id": shop["pepper"].id, "qty": 1}], "address": ADDRESS},
        format="json",
    )
    assert r.status_code == 409 and r.json()["code"] == "cart_changed"
    assert Order.objects.count() == 0


def test_seeded_database_is_immediately_orderable(settings, auth_client):
    """B8.1: seed_abo_samra data is orderable immediately; staff can log in."""
    settings.ADMIN_PHONE = "01000000000"
    settings.ADMIN_PASSWORD = "seed-admin-pass"
    call_command("seed_abo_samra")
    call_command("seed_abo_samra")  # idempotent
    assert Product.objects.count() == 16
    variant = ProductVariant.objects.filter(product__is_available=True, is_default=True).first()
    r = auth_client.post(
        "/api/v1/orders/",
        {"items": [{"variant_id": variant.id, "qty": 1}], "address": ADDRESS},
        format="json",
    )
    assert r.status_code == 201 and r.json()["number"] == 1001
    login = APIClient().post(
        "/api/v1/auth/admin/login/",
        {"phone": "01000000000", "password": "seed-admin-pass"},
        format="json",
    )
    assert login.status_code == 200


def _access(user):
    from apps.accounts.tokens import issue_tokens

    return issue_tokens(user)["access"]

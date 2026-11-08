from decimal import Decimal

import pytest

from apps.accounts.models import User
from apps.accounts.tokens import issue_tokens
from apps.catalog.tests.factories import CategoryFactory, make_product
from apps.core.models import ShopSettings
from apps.offers.tests.factories import bundle_offer, percentage_offer
from apps.orders.models import Order, OrderStatusLog
from apps.orders.services.orders import change_status

pytestmark = pytest.mark.django_db

URL = "/api/v1/orders/"
ADDRESS = "12 شارع التحرير، الدقي"


def post(client, items=(), bundles=(), **extra):
    body = {"items": list(items), "bundles": list(bundles), "address": ADDRESS, **extra}
    return client.post(URL, body, format="json")


def other_client(api_client_cls, user):
    client = api_client_cls()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user)['access']}")
    return client


def test_anonymous_cannot_order(api_client):
    _, v = make_product()
    assert post(api_client, [{"variant_id": v.id, "qty": 1}]).status_code == 401


def test_totals_match_quote_and_reference_case(auth_client, customer):
    spices = CategoryFactory(slug="spices")
    honey = CategoryFactory(slug="honey")
    _, cumin = make_product("كمون مطحون", 60, spices)
    _, pepper = make_product("فلفل أسود حب", 95, spices)
    _, honey_v = make_product("عسل نحل طبيعي", 220, honey, label="كيلو")
    offer = percentage_offer(15, category=spices, name="خصم 15% على كل البهارات")
    items = [
        {"variant_id": cumin.id, "qty": 2, "note": "ناعم"},
        {"variant_id": pepper.id, "qty": 1},
        {"variant_id": honey_v.id, "qty": 1},
    ]
    quote = auth_client.post("/api/v1/cart/quote/", {"items": items}, format="json").json()
    r = post(auth_client, items, area="الدقي")
    assert r.status_code == 201
    body = r.json()
    assert body["number"] == 1001
    assert body["status"] == "new"
    assert body["payment_method"] == "cod"
    assert body["customer"] == {"name": customer.name, "phone": customer.phone}
    assert (body["subtotal"], body["discount_total"], body["delivery_fee"], body["total"]) == (
        435, 32, 30, 433,
    )  # fmt: skip
    assert body["total"] == quote["total"]
    assert body["discounts"] == [
        {"offer_id": offer.id, "label": "خصم 15% على كل البهارات", "amount": 32}
    ]
    assert body["lines"][0] == {
        "name": "كمون مطحون", "unit_label": "ربع كيلو", "qty": 2,
        "unit_price": 60, "line_total": 120, "note": "ناعم",
    }  # fmt: skip
    log = OrderStatusLog.objects.get()
    assert (log.from_status, log.to_status, log.changed_by) == (None, "new", customer)


def test_number_sequence_increments_from_1001(auth_client):
    _, v = make_product()
    numbers = [
        post(auth_client, [{"variant_id": v.id, "qty": 1}]).json()["number"] for _ in range(3)
    ]
    assert numbers == [1001, 1002, 1003]


def test_address_saved_to_profile(auth_client, customer):
    _, v = make_product()
    post(auth_client, [{"variant_id": v.id, "qty": 1}], area="المعادي")
    customer.refresh_from_db()
    assert (customer.default_address, customer.area) == (ADDRESS, "المعادي")


def test_snapshots_survive_price_change(auth_client):
    _, v = make_product("كمون", 60)
    oid = post(auth_client, [{"variant_id": v.id, "qty": 2}]).json()["id"]
    v.price = Decimal("999")
    v.save()
    line = auth_client.get(f"{URL}{oid}/").json()["lines"][0]
    assert (line["unit_price"], line["line_total"]) == (60, 120)


def test_address_validation(auth_client):
    _, v = make_product()
    r = auth_client.post(
        URL, {"items": [{"variant_id": v.id, "qty": 1}], "address": "قصير"}, format="json"
    )
    assert r.status_code == 400 and "address" in r.json()
    r = auth_client.post(URL, {"items": [{"variant_id": v.id, "qty": 1}]}, format="json")
    assert r.status_code == 400 and "address" in r.json()


def test_cart_changed_409_with_fresh_quote(auth_client):
    product, v = make_product()
    product.is_available = False
    product.save()
    r = post(auth_client, [{"variant_id": v.id, "qty": 1}])
    assert r.status_code == 409
    body = r.json()
    assert body["code"] == "cart_changed"
    assert body["detail"] == "فيه حاجات في السلة اتغيرت"
    assert body["quote"]["warnings"][0]["code"] == "unavailable"
    assert Order.objects.count() == 0


def test_empty_cart_is_409(auth_client):
    assert post(auth_client).status_code == 409


def test_503_when_not_accepting_orders(auth_client):
    ShopSettings.objects.update_or_create(pk=1, defaults={"is_accepting_orders": False})
    _, v = make_product()
    r = post(auth_client, [{"variant_id": v.id, "qty": 1}])
    assert r.status_code == 503
    assert r.json()["detail"] == "المحل مش بياخد طلبات دلوقتي"


def test_stock_decremented_with_stock_factor(auth_client):
    product, v = make_product("كمون", 60, stock_qty=Decimal("10"), stock_unit="كيلو")
    v.stock_factor = Decimal("0.25")
    v.save()
    oid = post(auth_client, [{"variant_id": v.id, "qty": 6}]).json()["id"]
    product.refresh_from_db()
    assert product.stock_qty == Decimal("8.5")
    assert Order.objects.get(pk=oid).stock_deductions == {str(product.id): "1.500"}


def test_untracked_stock_untouched(auth_client):
    product, v = make_product()
    post(auth_client, [{"variant_id": v.id, "qty": 3}])
    product.refresh_from_db()
    assert product.stock_qty is None


def test_insufficient_stock_is_409(auth_client):
    _, v = make_product(stock_qty=Decimal("2"))
    r = post(auth_client, [{"variant_id": v.id, "qty": 3}])
    assert r.status_code == 409
    assert r.json()["quote"]["warnings"][0]["code"] == "insufficient_stock"


def test_bundle_items_decrement_stock(auth_client):
    p1, v1 = make_product("ينسون", 50, stock_qty=Decimal("5"))
    p2, v2 = make_product("عسل", 220, stock_qty=Decimal("5"), label="ربع كيلو")
    v2.stock_factor = Decimal("0.25")
    v2.save()
    offer = bundle_offer([(v1, 1), (v2, 2)], price=290)
    r = post(auth_client, bundles=[{"offer_id": offer.id, "qty": 2}])
    assert r.status_code == 201
    body = r.json()
    assert body["subtotal"] == 580 and body["lines"][0]["name"] == offer.name
    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p1.stock_qty == Decimal("3")
    assert p2.stock_qty == Decimal("4")  # 2 bundles * 2 items * 0.25


def test_bundle_cancel_restores_stock(auth_client, staff):
    p1, v1 = make_product("ينسون", 50, stock_qty=Decimal("5"))
    p2, v2 = make_product("عسل", 220, stock_qty=Decimal("5"))
    offer = bundle_offer([(v1, 1), (v2, 1)], price=200)
    oid = post(auth_client, bundles=[{"offer_id": offer.id, "qty": 2}]).json()["id"]
    change_status(Order.objects.get(pk=oid), "cancelled", staff)
    p1.refresh_from_db()
    p2.refresh_from_db()
    assert (p1.stock_qty, p2.stock_qty) == (Decimal("5"), Decimal("5"))


def test_notify_hook_called_after_commit(
    auth_client, monkeypatch, django_capture_on_commit_callbacks
):
    calls = []
    monkeypatch.setattr("apps.orders.services.orders.notify_new_order", calls.append)
    _, v = make_product()
    with django_capture_on_commit_callbacks(execute=True):
        post(auth_client, [{"variant_id": v.id, "qty": 1}])
    assert len(calls) == 1 and calls[0].number == 1001


def test_orders_throttle(auth_client, set_rate):
    set_rate("orders", "2/minute")
    _, v = make_product()
    codes = [post(auth_client, [{"variant_id": v.id, "qty": 1}]).status_code for _ in range(3)]
    assert codes == [201, 201, 429]


# ---- customer endpoints / permissions ---------------------------------------


def test_mine_is_paginated_newest_first_and_own_only(auth_client, customer, api_client):
    _, v = make_product()
    ids = [post(auth_client, [{"variant_id": v.id, "qty": 1}]).json()["id"] for _ in range(2)]
    stranger = User.objects.create_user(phone="01234567890", name="غريب")
    stranger_client = other_client(type(api_client), stranger)
    post(stranger_client, [{"variant_id": v.id, "qty": 1}])
    r = auth_client.get("/api/v1/orders/mine/")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"count", "next", "previous", "results"}
    assert body["count"] == 2
    assert [o["id"] for o in body["results"]] == ids[::-1]


def test_other_customers_order_is_404(auth_client, api_client):
    _, v = make_product()
    stranger = User.objects.create_user(phone="01234567890", name="غريب")
    oid = post(other_client(type(api_client), stranger), [{"variant_id": v.id, "qty": 1}]).json()[
        "id"
    ]
    assert auth_client.get(f"{URL}{oid}/").status_code == 404


def test_own_order_detail_shape(auth_client):
    _, v = make_product()
    oid = post(auth_client, [{"variant_id": v.id, "qty": 1}], notes="بدون شطة").json()["id"]
    body = auth_client.get(f"{URL}{oid}/").json()
    assert set(body) == {
        "id", "number", "status", "created_at", "customer", "address", "area", "notes",
        "lines", "subtotal", "discounts", "discount_total", "delivery_fee", "total",
        "payment_method",
    }  # fmt: skip


def test_mine_requires_auth(api_client):
    assert api_client.get("/api/v1/orders/mine/").status_code == 401


def test_customer_cannot_use_admin_endpoints(auth_client):
    for path in ("dashboard/", "orders/", "orders/counts/", "products/", "offers/", "customers/"):
        assert auth_client.get(f"/api/v1/admin/{path}").status_code == 403, path


def test_anonymous_cannot_use_admin_endpoints(api_client):
    assert api_client.get("/api/v1/admin/orders/").status_code == 401


def test_orders_list_query_count_constant(auth_client, django_assert_max_num_queries):
    _, v = make_product()
    for _ in range(5):
        post(auth_client, [{"variant_id": v.id, "qty": 1}])
    with django_assert_max_num_queries(6):
        assert auth_client.get("/api/v1/orders/mine/").status_code == 200

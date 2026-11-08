from decimal import Decimal

import pytest

from apps.catalog.tests.factories import make_product
from apps.orders.models import Order, OrderStatusLog

pytestmark = pytest.mark.django_db


@pytest.fixture
def order(auth_client):
    product, v = make_product("كمون مطحون", 60, stock_qty=Decimal("10"))
    r = auth_client.post(
        "/api/v1/orders/",
        {"items": [{"variant_id": v.id, "qty": 4}], "address": "12 شارع التحرير، الدقي"},
        format="json",
    )
    order = Order.objects.get(pk=r.json()["id"])
    order.product = product
    return order


def patch(client, order, status):
    return client.patch(f"/api/v1/admin/orders/{order.id}/", {"status": status}, format="json")


def test_valid_chain_logs_each_change(admin_client, order, staff):
    for status in ("preparing", "out_for_delivery", "delivered"):
        r = patch(admin_client, order, status)
        assert r.status_code == 200 and r.json()["status"] == status
    logs = list(OrderStatusLog.objects.filter(order=order).values_list("from_status", "to_status"))
    assert logs == [
        (None, "new"), ("new", "preparing"), ("preparing", "out_for_delivery"),
        ("out_for_delivery", "delivered"),
    ]  # fmt: skip
    assert OrderStatusLog.objects.filter(order=order).last().changed_by == staff


def test_invalid_jump_400_arabic(admin_client, order):
    r = patch(admin_client, order, "delivered")
    assert r.status_code == 400
    assert r.json()["detail"] == "مينفعش تغيّر الحالة من جديد لـ اتسلم"
    assert r.json()["code"] == "invalid_transition"
    order.refresh_from_db()
    assert order.status == "new"


@pytest.mark.parametrize("final", ["delivered", "cancelled"])
def test_final_states_are_final(admin_client, order, final):
    Order.objects.filter(pk=order.pk).update(status=final)
    assert patch(admin_client, order, "preparing").status_code == 400


def test_unknown_status_400(admin_client, order):
    assert patch(admin_client, order, "banana").status_code == 400


def test_patch_accepts_status_only(admin_client, order):
    r = admin_client.patch(
        f"/api/v1/admin/orders/{order.id}/", {"total": 1, "address": "x"}, format="json"
    )
    assert r.status_code == 400  # status missing


@pytest.mark.parametrize("path", ["new", "preparing", "out_for_delivery"])
def test_cancel_restores_stock_from_any_open_state(admin_client, order, path):
    order.product.refresh_from_db()
    assert order.product.stock_qty == Decimal("6")
    steps = {
        "new": [],
        "preparing": ["preparing"],
        "out_for_delivery": ["preparing", "out_for_delivery"],
    }
    for s in steps[path]:
        patch(admin_client, order, s)
    assert patch(admin_client, order, "cancelled").status_code == 200
    order.product.refresh_from_db()
    assert order.product.stock_qty == Decimal("10")


def test_cancel_twice_does_not_double_restore(admin_client, order):
    patch(admin_client, order, "cancelled")
    assert patch(admin_client, order, "cancelled").status_code == 400
    order.product.refresh_from_db()
    assert order.product.stock_qty == Decimal("10")


def test_customer_cannot_patch_status(auth_client, order):
    assert patch(auth_client, order, "preparing").status_code == 403


def test_admin_detail_has_items_summary(admin_client, order):
    body = admin_client.get(f"/api/v1/admin/orders/{order.id}/").json()
    assert body["items_summary"] == "كمون مطحون ×4"
    assert body["customer"]["phone"] == order.customer.phone


def test_admin_list_unknown_status_400(admin_client):
    r = admin_client.get("/api/v1/admin/orders/?status=zzz")
    assert r.status_code == 400
    assert r.json() == {"status": ["الحالة دي مش موجودة"]}
    assert admin_client.get("/api/v1/admin/orders/?status=new").status_code == 200

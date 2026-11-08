from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.tests.factories import make_product
from apps.orders.models import Order, OrderLine

pytestmark = pytest.mark.django_db
BASE = "/api/v1/admin/"


def make_order(
    customer, total=100, status="new", created_at=None, lines=(("كمون", 1),), number=None
):
    n = number or (Order.objects.count() + 1001)
    order = Order.objects.create(
        number=n, customer=customer, status=status, address="عنوان طويل كفاية",
        subtotal=total, total=total,
    )  # fmt: skip
    for name, qty in lines:
        OrderLine.objects.create(
            order=order, name=name, qty=qty, unit_price=total, line_total=total * qty
        )
    if created_at:
        Order.objects.filter(pk=order.pk).update(created_at=created_at)
    return order


def test_dashboard(admin_client, customer, staff):
    make_order(customer, 100)
    make_order(customer, 50, status="cancelled")
    make_order(customer, 25, status="preparing")
    make_order(customer, 999, created_at=timezone.now() - timedelta(days=3))
    old = User.objects.create_user(phone="01234567890", name="قديم")
    User.objects.filter(pk=old.pk).update(date_joined=timezone.now() - timedelta(days=30))
    p, _ = make_product(
        "كمون", stock_qty=Decimal("1.5"), low_stock_threshold=Decimal("2"), stock_unit="كيلو"
    )
    make_product("وفير", stock_qty=Decimal("50"), low_stock_threshold=Decimal("2"))
    make_product("غير متابع")
    body = admin_client.get(f"{BASE}dashboard/").json()
    assert set(body) == {
        "orders_today",
        "sales_today",
        "pending_count",
        "new_customers_week",
        "low_stock",
    }
    assert body["orders_today"] == 3
    assert body["sales_today"] == 125  # cancelled excluded
    assert body["pending_count"] == 2
    assert body["new_customers_week"] == 1  # customer (staff and old excluded)
    assert body["low_stock"] == [
        {"id": p.id, "name": "كمون", "stock_qty": 1.5, "stock_unit": "كيلو"}
    ]


def test_dashboard_pending_count(admin_client, customer):
    make_order(customer, status="new")
    make_order(customer, status="new", created_at=timezone.now() - timedelta(days=5))
    make_order(customer, status="preparing")
    assert admin_client.get(f"{BASE}dashboard/").json()["pending_count"] == 2


def test_dashboard_today_uses_cairo_midnight(admin_client, customer):
    from zoneinfo import ZoneInfo

    cairo_midnight = timezone.localtime(timezone.now(), ZoneInfo("Africa/Cairo")).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    make_order(customer, 10, created_at=cairo_midnight + timedelta(minutes=1))
    make_order(customer, 20, created_at=cairo_midnight - timedelta(minutes=1))
    assert admin_client.get(f"{BASE}dashboard/").json()["orders_today"] == 1


def test_orders_list_filters_and_search(admin_client, customer):
    other = User.objects.create_user(phone="01234567890", name="منى")
    a = make_order(customer, status="new")
    b = make_order(other, status="preparing")
    results = lambda qs: [o["id"] for o in admin_client.get(f"{BASE}orders/{qs}").json()["results"]]  # noqa: E731
    assert results("") == [b.id, a.id]  # newest first
    assert results("?status=preparing") == [b.id]
    assert results(f"?q={a.number}") == [a.id]
    assert results("?q=منى") == [b.id]
    assert results("?q=01234567890") == [b.id]
    assert results("?q=%2B201234567890") == [b.id]  # +20 normalized
    assert results("?q=%D9%A0%D9%A1%D9%A2%D9%A3%D9%A4%D9%A5%D9%A6%D9%A7%D9%A8%D9%A9%D9%A0") == [
        b.id
    ]


def test_orders_list_shape_pagination_and_items_summary(admin_client, customer):
    make_order(customer, lines=(("كمون مطحون", 2), ("فلفل أسود", 1), ("عسل نحل", 1)))
    body = admin_client.get(f"{BASE}orders/").json()
    assert set(body) == {"count", "next", "previous", "results"}
    row = body["results"][0]
    assert row["items_summary"] == "كمون مطحون ×2، فلفل أسود، عسل نحل"
    assert row["customer"]["phone"] == customer.phone


def test_orders_list_no_n_plus_one(admin_client, customer, django_assert_max_num_queries):
    for _ in range(8):
        make_order(customer, lines=(("أ", 1), ("ب", 2)))
    with django_assert_max_num_queries(8):
        assert admin_client.get(f"{BASE}orders/").status_code == 200


def test_counts(admin_client, customer):
    make_order(customer, status="new")
    make_order(customer, status="new")
    make_order(customer, status="delivered")
    assert admin_client.get(f"{BASE}orders/counts/").json() == {
        "new": 2, "preparing": 0, "out_for_delivery": 0, "delivered": 1, "cancelled": 0,
    }  # fmt: skip


def test_customers_stats_ordering_and_search(admin_client, customer, staff):
    ahmed = customer
    mona = User.objects.create_user(phone="01234567890", name="منى")
    never = User.objects.create_user(phone="01551112223", name="جديد")
    make_order(ahmed, 100)
    make_order(ahmed, 50, status="cancelled")
    last = make_order(mona, 300, created_at=timezone.now() + timedelta(hours=1))
    body = admin_client.get(f"{BASE}customers/").json()
    assert set(body) == {"count", "next", "previous", "results"}
    rows = body["results"]
    assert [r["id"] for r in rows] == [mona.id, ahmed.id, never.id]  # nulls last, staff excluded
    assert rows[0]["total_spent"] == 300 and rows[0]["orders_count"] == 1
    assert rows[1]["orders_count"] == 2 and rows[1]["total_spent"] == 100  # cancelled not spent
    assert rows[2]["orders_count"] == 0 and rows[2]["total_spent"] == 0
    assert rows[2]["last_order_at"] is None and rows[0]["last_order_at"] is not None
    q = lambda v: [r["id"] for r in admin_client.get(f"{BASE}customers/?q={v}").json()["results"]]  # noqa: E731
    assert q("منى") == [mona.id]
    assert q("%2B201234567890") == [mona.id]
    assert q("0155") == [never.id]
    assert last.customer_id == mona.id


def test_customer_orders(admin_client, customer):
    other = User.objects.create_user(phone="01234567890", name="منى")
    mine = make_order(customer)
    make_order(other)
    r = admin_client.get(f"{BASE}customers/{customer.id}/orders/")
    assert [o["id"] for o in r.json()["results"]] == [mine.id]
    assert admin_client.get(f"{BASE}customers/99999/orders/").status_code == 404


def test_customers_no_n_plus_one(admin_client, customer, django_assert_max_num_queries):
    for i in range(6):
        make_order(User.objects.create_user(phone=f"0155111222{i}", name=f"ع{i}"))
    with django_assert_max_num_queries(4):
        assert admin_client.get(f"{BASE}customers/").status_code == 200

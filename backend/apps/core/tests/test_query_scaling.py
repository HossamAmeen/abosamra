"""QA-05: N+1 budget. List endpoints must issue the same number of queries for 2 rows and 12 rows.

PA_CHECKLIST rows verified: A2.1, A3.1, A4.1, A5.1, B6.4 (list shapes stay cheap).
"""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.accounts.models import User
from apps.catalog.tests.factories import CategoryFactory, make_product
from apps.offers.tests.factories import bundle_offer, percentage_offer
from apps.orders.models import Order, OrderLine

pytestmark = pytest.mark.django_db


def grow(n):
    """Add n more rows of everything the lists join over."""
    cat = CategoryFactory(slug=f"c{Order.objects.count()}-{n}")
    customers = []
    for i in range(n):
        customers.append(
            User.objects.create_user(
                phone=f"015{(User.objects.count() + 10000000):08d}", name=f"عميل {i}"
            )
        )
    variants = []
    for i in range(n):
        _, v = make_product(f"منتج {cat.slug}-{i}", 50 + i, cat)
        variants.append(v)
    for i, customer in enumerate(customers):
        order = Order.objects.create(
            number=Order.objects.count() + 1001,
            customer=customer,
            status="new",
            address="عنوان طويل كفاية",
            subtotal=100,
            total=100,
        )
        for v in variants[i : i + 2] or variants[:1]:
            OrderLine.objects.create(
                order=order, variant=v, name=v.product.name, qty=1, unit_price=50, line_total=50
            )
    for _ in range(max(1, n // 3)):
        bundle_offer([(variants[0], 1), (variants[-1], 1)])
        percentage_offer(10, category=cat)


def count_queries(client, url):
    with CaptureQueriesContext(connection) as ctx:
        r = client.get(url)
    assert r.status_code == 200
    return len(ctx)


LISTS = [
    ("admin", "/api/v1/admin/orders/"),
    ("admin", "/api/v1/admin/orders/?status=new"),
    ("admin", "/api/v1/admin/products/"),
    ("admin", "/api/v1/admin/offers/"),
    ("admin", "/api/v1/admin/customers/"),
    ("admin", "/api/v1/admin/dashboard/"),
    ("customer", "/api/v1/orders/mine/"),
    ("anon", "/api/v1/products/"),
    ("anon", "/api/v1/products/?category=all"),
    ("anon", "/api/v1/offers/active/"),
    ("anon", "/api/v1/categories/"),
]


@pytest.mark.parametrize(("who", "url"), LISTS, ids=[u for _, u in LISTS])
def test_list_query_count_does_not_grow_with_rows(request, who, url, customer):
    client = {
        "admin": lambda: request.getfixturevalue("admin_client"),
        "customer": lambda: request.getfixturevalue("auth_client"),
        "anon": lambda: request.getfixturevalue("api_client"),
    }[who]()
    grow(2)
    # give the logged-in customer some orders as well
    if who == "customer":
        for _ in range(2):
            Order.objects.create(
                number=Order.objects.count() + 1001, customer=customer, address="عنوان طويل كفاية",
                subtotal=10, total=10,
            )  # fmt: skip
    small = count_queries(client, url)
    grow(12)
    if who == "customer":
        for _ in range(10):
            Order.objects.create(
                number=Order.objects.count() + 1001, customer=customer, address="عنوان طويل كفاية",
                subtotal=10, total=10,
            )  # fmt: skip
    large = count_queries(client, url)
    assert large <= small, f"{url}: {small} queries for few rows, {large} for many (N+1)"

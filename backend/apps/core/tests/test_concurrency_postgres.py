"""QA-05 / FIX-12: concurrent order creation. PostgreSQL only.

Skipped unless the active database is PostgreSQL (the test settings use in-memory SQLite, which
cannot run real concurrent transactions). To run it against a local PostgreSQL:

    DATABASE_URL=postgres://user:pass@localhost:5432/abosamra_test \\
    DJANGO_SETTINGS_MODULE=config.settings.test_pg \\
    pytest apps/core/tests/test_concurrency_postgres.py

where `config.settings.test_pg` is any settings module that imports `.test` and overrides
DATABASES from DATABASE_URL (not shipped; test settings currently force SQLite).

PA_CHECKLIST rows verified when run on PostgreSQL: B4.6 (sequence-backed unique numbers) and B4.2
(stock never oversold under concurrency).
"""

import threading
from decimal import Decimal

import pytest
from django.db import connection, connections

from apps.accounts.models import User
from apps.accounts.tokens import issue_tokens
from apps.catalog.tests.factories import make_product
from apps.orders.models import Order

pytestmark = pytest.mark.skipif(
    connection.vendor != "postgresql", reason="needs PostgreSQL (real concurrent transactions)"
)


@pytest.mark.django_db(transaction=True)
def test_three_concurrent_orders_get_unique_sequential_numbers_and_correct_stock():
    from rest_framework.test import APIClient

    product, variant = make_product("كمون", 60, stock_qty=Decimal("10"))
    users = [User.objects.create_user(phone=f"0151000000{i}", name=f"u{i}") for i in range(3)]
    results, barrier = [], threading.Barrier(3)

    def place(user):
        try:
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user)['access']}")
            barrier.wait(timeout=10)
            r = client.post(
                "/api/v1/orders/",
                {
                    "items": [{"variant_id": variant.id, "qty": 2}],
                    "address": "12 شارع التحرير، الدقي",
                },
                format="json",
            )
            results.append((r.status_code, r.json().get("number")))
        finally:
            connections.close_all()

    threads = [threading.Thread(target=place, args=(u,)) for u in users]
    [t.start() for t in threads]
    [t.join(timeout=30) for t in threads]

    assert sorted(code for code, _ in results) == [201, 201, 201]
    assert sorted(n for _, n in results) == [1001, 1002, 1003]
    product.refresh_from_db()
    assert product.stock_qty == Decimal("4")
    assert Order.objects.count() == 3

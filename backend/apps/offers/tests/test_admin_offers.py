from datetime import timedelta

import pytest
from django.utils import timezone

from apps.catalog.tests.factories import CategoryFactory, make_product
from apps.offers.models import Offer
from apps.offers.tests.factories import bundle_offer, percentage_offer

pytestmark = pytest.mark.django_db
URL = "/api/v1/admin/offers/"


def test_list_is_plain_array_including_inactive(admin_client):
    percentage_offer(10)
    percentage_offer(20, is_active=False)
    r = admin_client.get(URL)
    assert r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) == 2
    assert {"is_active", "target", "bundle_items", "old_price"} <= set(r.json()[0])


def test_create_percentage_category(admin_client):
    cat = CategoryFactory(slug="spices")
    r = admin_client.post(
        URL,
        {
            "type": "percentage",
            "name": "خصم",
            "value": 15,
            "target": {"kind": "category", "slug": "spices"},
        },
        format="json",
    )
    assert r.status_code == 201, r.json()
    body = r.json()
    assert body["value"] == 15 and body["target"] == {
        "kind": "category",
        "slug": "spices",
        "ids": [],
    }
    assert Offer.objects.get().target_category == cat


def test_create_percentage_products_and_roundtrip(admin_client):
    p1, _ = make_product("أ")
    p2, _ = make_product("ب")
    r = admin_client.post(
        URL,
        {
            "type": "percentage",
            "name": "خصم",
            "value": 10,
            "target": {"kind": "products", "ids": [p1.id, p2.id]},
        },
        format="json",
    )
    assert r.status_code == 201
    assert r.json()["target"]["ids"] == sorted([p1.id, p2.id])


@pytest.mark.parametrize("value", [0, 91, None])
def test_percentage_value_range(admin_client, value):
    r = admin_client.post(URL, {"type": "percentage", "name": "x", "value": value}, format="json")
    assert r.status_code == 400 and "value" in r.json()


def test_percentage_products_target_needs_products(admin_client):
    r = admin_client.post(
        URL,
        {"type": "percentage", "name": "x", "value": 10, "target": {"kind": "products", "ids": []}},
        format="json",
    )
    assert r.status_code == 400 and "target" in r.json()


def test_percentage_category_target_needs_valid_slug(admin_client):
    r = admin_client.post(
        URL,
        {
            "type": "percentage",
            "name": "x",
            "value": 10,
            "target": {"kind": "category", "slug": "nope"},
        },
        format="json",
    )
    assert r.status_code == 400


def test_create_bundle(admin_client):
    _, v1 = make_product("أ", 50)
    _, v2 = make_product("ب", 60)
    r = admin_client.post(
        URL,
        {
            "type": "bundle", "name": "باكدج", "bundle_price": 90,
            "bundle_items": [{"variant_id": v1.id, "qty": 1}, {"variant_id": v2.id, "qty": 2}],
        },
        format="json",
    )  # fmt: skip
    assert r.status_code == 201, r.json()
    body = r.json()
    assert body["bundle_price"] == 90 and body["old_price"] == 170
    assert body["bundle_items"][1] == {
        "variant_id": v2.id,
        "name": f"{v2.product.name} ربع كيلو",
        "qty": 2,
    }


def test_bundle_needs_two_items_calls_validate_relations(admin_client):
    _, v1 = make_product("أ")
    r = admin_client.post(
        URL,
        {
            "type": "bundle",
            "name": "باكدج",
            "bundle_price": 90,
            "bundle_items": [{"variant_id": v1.id, "qty": 1}],
        },
        format="json",
    )
    assert r.status_code == 400 and "bundle_items" in r.json()
    assert Offer.objects.count() == 0  # rolled back


def test_bundle_missing_price_and_unknown_variant(admin_client):
    _, v1 = make_product("أ")
    items = [{"variant_id": v1.id, "qty": 1}, {"variant_id": 9999, "qty": 1}]
    r = admin_client.post(
        URL,
        {"type": "bundle", "name": "x", "bundle_price": 5, "bundle_items": items},
        format="json",
    )
    assert r.status_code == 400 and "bundle_items" in r.json()
    r = admin_client.post(
        URL, {"type": "bundle", "name": "x", "bundle_items": items[:1]}, format="json"
    )
    assert r.status_code == 400 and "bundle_price" in r.json()


def test_free_delivery_min_order(admin_client):
    r = admin_client.post(
        URL, {"type": "free_delivery", "name": "توصيل", "min_order": 500}, format="json"
    )
    assert r.status_code == 201 and r.json()["min_order"] == 500
    r = admin_client.post(URL, {"type": "free_delivery", "name": "توصيل"}, format="json")
    assert r.status_code == 400 and "min_order" in r.json()


def test_ends_before_start_rejected(admin_client):
    now = timezone.now()
    r = admin_client.post(
        URL,
        {"type": "free_delivery", "name": "x", "min_order": 5, "starts_at": now.isoformat(),
         "ends_at": (now - timedelta(days=1)).isoformat()},
        format="json",
    )  # fmt: skip
    assert r.status_code == 400 and "ends_at" in r.json()


def test_patch_is_active_switch(admin_client):
    offer = percentage_offer(15)
    r = admin_client.patch(f"{URL}{offer.id}/", {"is_active": False}, format="json")
    assert r.status_code == 200 and r.json()["is_active"] is False
    offer.refresh_from_db()
    assert not offer.is_active
    assert admin_client.get("/api/v1/offers/active/").json() == []


def test_patch_replaces_bundle_items(admin_client):
    _, v1 = make_product("أ")
    _, v2 = make_product("ب")
    _, v3 = make_product("ج")
    offer = bundle_offer([(v1, 1), (v2, 1)])
    r = admin_client.patch(
        f"{URL}{offer.id}/",
        {"bundle_items": [{"variant_id": v3.id, "qty": 3}, {"variant_id": v1.id, "qty": 1}]},
        format="json",
    )
    assert r.status_code == 200
    assert sorted(i["variant_id"] for i in r.json()["bundle_items"]) == sorted([v1.id, v3.id])
    r = admin_client.patch(
        f"{URL}{offer.id}/", {"bundle_items": [{"variant_id": v1.id, "qty": 1}]}, format="json"
    )
    assert r.status_code == 400


def test_patch_target_switch_clears_products(admin_client):
    p, _ = make_product("أ")
    cat = CategoryFactory(slug="herbs")
    offer = percentage_offer(10, products=[p])
    r = admin_client.patch(
        f"{URL}{offer.id}/", {"target": {"kind": "category", "slug": "herbs"}}, format="json"
    )
    assert r.status_code == 200
    offer.refresh_from_db()
    assert offer.target_category == cat and offer.target_products.count() == 0


def test_delete_offer(admin_client):
    offer = percentage_offer(10)
    assert admin_client.delete(f"{URL}{offer.id}/").status_code == 204
    assert Offer.objects.count() == 0


def test_permissions(auth_client):
    from rest_framework.test import APIClient

    api_client = APIClient()
    assert auth_client.get(URL).status_code == 403
    assert api_client.post(URL, {}, format="json").status_code == 401


def test_list_query_budget(admin_client, django_assert_max_num_queries):
    _, v1 = make_product("أ")
    _, v2 = make_product("ب")
    for _ in range(6):
        bundle_offer([(v1, 1), (v2, 1)])
    with django_assert_max_num_queries(6):
        assert admin_client.get(URL).status_code == 200

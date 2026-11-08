from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.tests.factories import CategoryFactory, make_product
from apps.offers.models import Offer

from .factories import bundle_offer, expired, free_delivery_offer, percentage_offer

pytestmark = pytest.mark.django_db

ACTIVE = "/api/v1/offers/active/"


# --- live manager --------------------------------------------------------
def test_live_filters_inactive_expired_and_future():
    now = timezone.now() + timedelta(seconds=5)
    live = percentage_offer(10, name="live")
    percentage_offer(10, name="open-ended", ends_at=None)
    percentage_offer(10, name="off", is_active=False)
    percentage_offer(10, name="future", starts_at=now + timedelta(days=1))
    percentage_offer(10, name="expired", **expired())
    percentage_offer(10, name="ends-now", starts_at=now - timedelta(days=1), ends_at=now)
    names = set(Offer.objects.live(now).values_list("name", flat=True))
    assert names == {"live", "open-ended"}
    assert live in Offer.objects.live()


# --- validation ----------------------------------------------------------
@pytest.mark.parametrize("value", [None, 0, 91, 100])
def test_percentage_value_must_be_1_to_90(value):
    offer = Offer(type="percentage", name="x", value=value, target_kind="all")
    with pytest.raises(ValidationError) as exc:
        offer.full_clean()
    assert "value" in exc.value.message_dict


@pytest.mark.parametrize("value", [1, 90])
def test_percentage_boundaries_ok(value):
    Offer(type="percentage", name="x", value=value, target_kind="all").full_clean()


def test_percentage_category_target_requires_category():
    offer = Offer(type="percentage", name="x", value=10, target_kind="category")
    with pytest.raises(ValidationError) as exc:
        offer.full_clean()
    assert "target_category" in exc.value.message_dict
    offer.target_category = CategoryFactory()
    offer.full_clean()


def test_percentage_products_target_requires_products():
    offer = percentage_offer(10, name="p")
    offer.target_kind = "products"
    with pytest.raises(ValidationError) as exc:
        offer.validate_relations()
    assert "target_products" in exc.value.message_dict
    _, v = make_product()
    offer.target_products.add(v.product)
    offer.validate_relations()


def test_bundle_requires_price_and_two_items():
    offer = Offer(type="bundle", name="b")
    with pytest.raises(ValidationError) as exc:
        offer.full_clean()
    assert "bundle_price" in exc.value.message_dict

    _, v1 = make_product(name="أ")
    _, v2 = make_product(name="ب")
    offer = bundle_offer([(v1, 1)], price=100)
    with pytest.raises(ValidationError) as exc:
        offer.validate_relations()
    assert "bundle_items" in exc.value.message_dict
    offer.bundle_items.create(variant=v2, qty=1)
    offer.validate_relations()


def test_free_delivery_requires_min_order():
    with pytest.raises(ValidationError) as exc:
        Offer(type="free_delivery", name="f").full_clean()
    assert "min_order" in exc.value.message_dict
    Offer(type="free_delivery", name="f", min_order=500).full_clean()


def test_ends_at_must_be_after_starts_at():
    now = timezone.now()
    offer = Offer(
        type="free_delivery", name="f", min_order=1, starts_at=now, ends_at=now - timedelta(days=1)
    )
    with pytest.raises(ValidationError) as exc:
        offer.full_clean()
    assert "ends_at" in exc.value.message_dict


# --- /offers/active/ -----------------------------------------------------
def test_active_lists_only_live_featured_first(api_client):
    spices = CategoryFactory(slug="spices")
    percentage_offer(15, category=spices, name="عادي")
    percentage_offer(20, category=spices, name="مميز", is_featured=True)
    percentage_offer(30, category=spices, name="منتهي", **expired())
    percentage_offer(40, category=spices, name="موقوف", is_active=False)
    r = api_client.get(ACTIVE)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert [o["name"] for o in body] == ["مميز", "عادي"]


def test_offer_shapes(api_client):
    spices = CategoryFactory(slug="spices")
    p, v = make_product(name="كركديه", price=65, category=spices)
    _, v2 = make_product(name="ينسون", price=50)
    percentage_offer(15, category=spices, name="بهارات")
    percentage_offer(10, products=[p], name="منتجات")
    percentage_offer(5, name="كله")
    bundle = bundle_offer([(v, 2), (v2, 1)], price=150, name="باكدج")
    free_delivery_offer(500)
    body = {o["name"]: o for o in api_client.get(ACTIVE).json()}

    keys = {
        "id", "type", "name", "description", "value", "target", "bundle_items",
        "bundle_price", "old_price", "min_order", "starts_at", "ends_at", "is_featured",
    }  # fmt: skip
    assert all(set(o) == keys for o in body.values())
    assert body["بهارات"]["target"] == {"kind": "category", "slug": "spices", "ids": []}
    assert body["بهارات"]["value"] == 15
    assert body["منتجات"]["target"] == {"kind": "products", "slug": None, "ids": [p.id]}
    assert body["كله"]["target"] == {"kind": "all", "slug": None, "ids": []}
    b = body["باكدج"]
    assert b["id"] == bundle.id
    assert b["bundle_price"] == 150
    assert b["old_price"] == 65 * 2 + 50
    assert b["bundle_items"] == [
        {"variant_id": v.id, "name": "كركديه ربع كيلو", "qty": 2},
        {"variant_id": v2.id, "name": "ينسون ربع كيلو", "qty": 1},
    ]
    fd = body["توصيل مجاني"]
    assert fd["min_order"] == 500 and fd["value"] is None and fd["old_price"] is None
    assert fd["bundle_items"] == [] and fd["bundle_price"] is None


def test_active_is_public_and_empty_ok(api_client):
    r = api_client.get(ACTIVE)
    assert r.status_code == 200 and r.json() == []

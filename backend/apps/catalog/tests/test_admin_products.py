import io
import json
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.catalog.models import Product
from apps.catalog.tests.factories import CategoryFactory, make_product
from apps.offers.tests.factories import bundle_offer
from apps.orders.models import Order, OrderLine

pytestmark = pytest.mark.django_db
URL = "/api/v1/admin/products/"

VARIANTS = [
    {"label": "ربع كيلو", "price": 60, "stock_factor": 0.25},
    {"label": "نص كيلو", "price": 115, "old_price": 130, "stock_factor": 0.5},
    {"label": "كيلو", "price": 220},
]


def png(size=(2000, 1000)):
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, "PNG")
    return SimpleUploadedFile("p.png", buf.getvalue(), content_type="image/png")


def multipart(cat, variants=VARIANTS, **extra):
    return {
        "name": "كمون مطحون",
        "category": cat.id,
        "description": "وصف",
        "is_available": "true",
        "variants": json.dumps(variants),
        **extra,
    }


def test_create_multipart_with_json_string_variants_and_image(admin_client):
    cat = CategoryFactory(slug="spices")
    r = admin_client.post(
        URL, multipart(cat, image=png(), stock_qty="10", stock_unit="كيلو"), format="multipart"
    )
    assert r.status_code == 201, r.json()
    body = r.json()
    assert body["slug"] and body["category"]["slug"] == "spices"
    assert [v["label"] for v in body["variants"]] == ["ربع كيلو", "نص كيلو", "كيلو"]
    assert [v["is_default"] for v in body["variants"]] == [True, False, False]
    assert body["variants"][1]["old_price"] == 130
    assert body["image"].startswith("http") and body["image"].endswith(".webp")
    assert body["stock_qty"] == 10
    product = Product.objects.get()
    assert product.variants.count() == 3
    assert product.stock_qty == Decimal("10")


def test_create_native_json_body_and_category_slug(admin_client):
    CategoryFactory(slug="herbs")
    r = admin_client.post(
        URL, {"name": "ينسون", "category": "herbs", "variants": VARIANTS[:1]}, format="json"
    )
    assert r.status_code == 201, r.json()
    assert r.json()["variants"][0]["is_default"] is True


@pytest.mark.parametrize(
    "variants",
    [[], "not json", "{}", [{"label": "", "price": 5}], [{"label": "كيلو"}]],
)
def test_variants_validation(admin_client, variants):
    cat = CategoryFactory()
    r = admin_client.post(URL, multipart(cat, variants=variants), format="multipart")
    assert r.status_code == 400 and "variants" in r.json()


def test_variants_required_on_create(admin_client):
    cat = CategoryFactory()
    r = admin_client.post(URL, {"name": "منتج", "category": cat.id}, format="json")
    assert r.status_code == 400 and "variants" in r.json()


def test_two_defaults_rejected(admin_client):
    cat = CategoryFactory()
    two = [{**VARIANTS[0], "is_default": True}, {**VARIANTS[1], "is_default": True}]
    r = admin_client.post(URL, multipart(cat, variants=two), format="multipart")
    assert r.status_code == 400 and "variants" in r.json()


def test_explicit_default_respected(admin_client):
    cat = CategoryFactory()
    v = [{**VARIANTS[0]}, {**VARIANTS[1], "is_default": True}]
    r = admin_client.post(URL, multipart(cat, variants=v), format="multipart")
    assert r.status_code == 201
    assert [x["is_default"] for x in r.json()["variants"]] == [True, False]  # default first
    assert r.json()["variants"][0]["label"] == "نص كيلو"


def test_invalid_category_and_name(admin_client):
    r = admin_client.post(URL, {"name": "x", "category": 999, "variants": VARIANTS}, format="json")
    assert r.status_code == 400 and {"name", "category"} <= set(r.json())


def test_patch_variants_replace_by_id(admin_client):
    product, v1 = make_product("كمون", 60)
    from apps.catalog.models import ProductVariant

    v2 = ProductVariant.objects.create(product=product, label="نص كيلو", price=115, order=1)
    v3 = ProductVariant.objects.create(product=product, label="كيلو", price=220, order=2)
    payload = [
        {"id": v1.id, "label": "ربع كيلو", "price": 65, "is_default": False},
        {"id": v3.id, "label": "كيلو", "price": 220, "is_default": True},
        {"label": "علبة", "price": 30},
    ]
    r = admin_client.patch(
        f"{URL}{product.id}/", {"variants": json.dumps(payload)}, format="multipart"
    )
    assert r.status_code == 200, r.json()
    body = r.json()
    ids = [v["id"] for v in body["variants"]]
    assert v2.id not in ids  # omitted -> deleted
    assert {v1.id, v3.id} <= set(ids) and len(ids) == 3
    assert body["variants"][0]["id"] == v3.id and body["variants"][0]["is_default"] is True
    v1.refresh_from_db()
    assert v1.price == 65
    assert product.variants.filter(is_default=True).count() == 1


def test_patch_foreign_variant_id_rejected(admin_client):
    product, _ = make_product("أ")
    _, other = make_product("ب")
    r = admin_client.patch(
        f"{URL}{product.id}/",
        {"variants": [{"id": other.id, "label": "س", "price": 1}]},
        format="json",
    )
    assert r.status_code == 400


def test_patch_availability_only_keeps_variants(admin_client):
    product, v = make_product("كمون")
    r = admin_client.patch(f"{URL}{product.id}/", {"is_available": False}, format="json")
    assert r.status_code == 200 and r.json()["is_available"] is False
    assert r.json()["variants"][0]["id"] == v.id


def test_patch_multipart_empty_stock_clears_it(admin_client):
    product, _ = make_product("كمون", stock_qty=Decimal("5"))
    r = admin_client.patch(f"{URL}{product.id}/", {"stock_qty": ""}, format="multipart")
    assert r.status_code == 200 and r.json()["stock_qty"] is None


def test_variant_in_bundle_cannot_be_removed(admin_client):
    p1, v1 = make_product("أ")
    _, v2 = make_product("ب")
    bundle_offer([(v1, 1), (v2, 1)])
    other = {"label": "جديد", "price": 5}
    r = admin_client.patch(f"{URL}{p1.id}/", {"variants": [other]}, format="json")
    assert r.status_code == 400


def test_list_filters_paginated_and_query_budget(admin_client, django_assert_max_num_queries):
    spices, herbs = CategoryFactory(slug="spices"), CategoryFactory(slug="herbs")
    make_product("كمون", category=spices)
    make_product("ينسون", category=herbs)
    gone, _ = make_product("خلصان", category=herbs, is_available=False)
    for i in range(10):
        make_product(f"م{i}", category=spices)
    with django_assert_max_num_queries(5):
        body = admin_client.get(URL).json()
    assert set(body) == {"count", "next", "previous", "results"} and body["count"] == 13
    ids = lambda qs: {p["id"] for p in admin_client.get(f"{URL}{qs}").json()["results"]}  # noqa: E731
    assert ids("?category=herbs") == {Product.objects.get(name="ينسون").id, gone.id}
    assert ids(f"?category={herbs.id}&is_available=false") == {gone.id}
    assert ids("?q=ينس") == {Product.objects.get(name="ينسون").id}


def test_delete_hard_when_no_orders(admin_client):
    product, _ = make_product("بدون طلبات")
    assert admin_client.delete(f"{URL}{product.id}/").status_code == 204
    assert not Product.objects.filter(pk=product.pk).exists()


def test_delete_soft_when_order_lines_exist(admin_client, customer):
    product, v = make_product("اتباع")
    order = Order.objects.create(
        number=1001, customer=customer, address="عنوان طويل كفاية", subtotal=60, total=60
    )
    OrderLine.objects.create(
        order=order, variant=v, name="اتباع", qty=1, unit_price=60, line_total=60
    )
    assert admin_client.delete(f"{URL}{product.id}/").status_code == 204
    product.refresh_from_db()
    assert product.is_archived and not product.is_available
    # hidden from catalog and from the admin list
    assert admin_client.get("/api/v1/products/").json()["count"] == 0
    assert admin_client.get(URL).json()["count"] == 0
    assert admin_client.get(f"{URL}{product.id}/").status_code == 404


def test_delete_soft_when_in_bundle(admin_client):
    p1, v1 = make_product("أ")
    _, v2 = make_product("ب")
    offer = bundle_offer([(v1, 1), (v2, 1)])
    assert admin_client.delete(f"{URL}{p1.id}/").status_code == 204
    assert offer.bundle_items.count() == 2
    assert Product.objects.get(pk=p1.pk).is_archived


def test_permissions(auth_client):
    from rest_framework.test import APIClient

    api_client = APIClient()
    assert auth_client.get(URL).status_code == 403
    assert auth_client.post(URL, {}, format="json").status_code == 403
    assert api_client.get(URL).status_code == 401

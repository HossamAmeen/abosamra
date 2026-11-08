import io
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from PIL import Image

from apps.offers.tests.factories import expired, percentage_offer

from .factories import CategoryFactory, ProductFactory, VariantFactory, make_product

pytestmark = pytest.mark.django_db

PRODUCTS = "/api/v1/products/"


def test_categories_unpaginated_ordered_active_only(api_client):
    CategoryFactory(slug="b", name="ب", order=2)
    CategoryFactory(slug="a", name="أ", order=1)
    CategoryFactory(slug="hidden", name="مخفي", order=0, is_active=False)
    r = api_client.get("/api/v1/categories/")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert [c["slug"] for c in body] == ["a", "b"]
    assert set(body[0]) == {"id", "slug", "name", "color", "icon", "order"}


def test_product_shape_variants_default_first_and_old_price(api_client):
    cat = CategoryFactory(slug="spices", name="بهارات", color="#F6D9B8", icon="soup")
    p = ProductFactory(category=cat, name="كمون مطحون", is_featured=True)
    VariantFactory(product=p, label="كيلو", price=220, is_default=False, order=2)
    VariantFactory(product=p, label="ربع كيلو", price=60, compare_at_price=Decimal("70"), order=0)
    VariantFactory(product=p, label="نص كيلو", price=115, is_default=False, order=1)
    body = api_client.get(PRODUCTS).json()["results"][0]
    assert set(body) == {
        "id", "slug", "name", "description", "image", "is_available", "is_featured",
        "category", "variants", "active_offer",
    }  # fmt: skip
    assert body["category"] == {
        "slug": "spices", "name": "بهارات", "color": "#F6D9B8", "icon": "soup"
    }  # fmt: skip
    assert [v["label"] for v in body["variants"]] == ["ربع كيلو", "نص كيلو", "كيلو"]
    assert body["variants"][0]["is_default"] is True
    assert body["variants"][0] == {
        "id": body["variants"][0]["id"], "label": "ربع كيلو", "price": 60, "old_price": 70,
        "is_default": True,
    }  # fmt: skip
    assert body["variants"][1]["old_price"] is None
    assert body["image"] is None
    assert body["active_offer"] is None


def test_image_is_absolute_url(api_client):
    buf = io.BytesIO()
    Image.new("RGB", (50, 50)).save(buf, format="PNG")
    p = ProductFactory(image=SimpleUploadedFile("a.png", buf.getvalue(), content_type="image/png"))
    VariantFactory(product=p)
    image = api_client.get(PRODUCTS).json()["results"][0]["image"]
    assert image.startswith("http://testserver/")
    assert image.endswith(".webp")


def test_pagination_envelope(api_client):
    for i in range(21):
        make_product(name=f"م{i}")
    body = api_client.get(PRODUCTS).json()
    assert body["count"] == 21 and len(body["results"]) == 20 and body["next"]
    assert len(api_client.get(PRODUCTS + "?page=2").json()["results"]) == 1


def test_visibility_inactive_category_and_archived_hidden_unavailable_listed(api_client):
    make_product(name="ظاهر")
    make_product(name="خلصان", is_available=False)
    make_product(name="مؤرشف", is_archived=True)
    make_product(name="قسم مخفي", category=CategoryFactory(is_active=False))
    r = api_client.get(PRODUCTS).json()
    names = {p["name"]: p for p in r["results"]}
    assert set(names) == {"ظاهر", "خلصان"}
    assert names["خلصان"]["is_available"] is False


def test_filters_category_all_q_featured(api_client):
    spices = CategoryFactory(slug="spices")
    herbs = CategoryFactory(slug="herbs")
    make_product(name="كمون", category=spices, is_featured=True)
    make_product(name="كركديه", category=herbs, description="مشروب ساخن")
    make_product(name="ينسون", category=herbs)

    def names(qs):
        return {p["name"] for p in api_client.get(PRODUCTS + qs).json()["results"]}

    assert names("?category=spices") == {"كمون"}
    assert names("?category=herbs") == {"كركديه", "ينسون"}
    assert names("?category=all") == {"كمون", "كركديه", "ينسون"}
    assert names("?q=ساخن") == {"كركديه"}  # description match
    assert names("?q=كمو") == {"كمون"}
    assert names("?featured=true") == {"كمون"}
    assert names("?category=herbs&q=ينس") == {"ينسون"}


def test_discounted_filter(api_client):
    spices = CategoryFactory(slug="spices")
    herbs = CategoryFactory(slug="herbs")
    nuts = CategoryFactory(slug="nuts")
    p_old, v = make_product(name="قديم", category=nuts)
    v.compare_at_price = Decimal("80")
    v.save()
    make_product(name="كمون", category=spices)
    make_product(name="ينسون", category=herbs)
    target, _ = make_product(name="منتج مستهدف", category=nuts)
    make_product(name="عادي", category=nuts)
    percentage_offer(15, category=spices)
    percentage_offer(10, products=[target], name="مستهدف")
    percentage_offer(50, category=herbs, **expired())

    got = {p["name"] for p in api_client.get(PRODUCTS + "?discounted=true").json()["results"]}
    assert got == {"قديم", "كمون", "منتج مستهدف"}
    assert len(api_client.get(PRODUCTS + "?discounted=false").json()["results"]) == 5


def test_discounted_with_all_offer_returns_everything(api_client):
    make_product(name="أ")
    make_product(name="ب")
    percentage_offer(5)
    assert len(api_client.get(PRODUCTS + "?discounted=true").json()["results"]) == 2


def test_detail_by_slug_including_unicode_and_hidden_404(api_client):
    p, _ = make_product(name="كمون مطحون")
    r = api_client.get(f"{PRODUCTS}{p.slug}/")
    assert r.status_code == 200 and r.json()["name"] == "كمون مطحون"
    hidden, _ = make_product(name="مؤرشف", is_archived=True)
    assert api_client.get(f"{PRODUCTS}{hidden.slug}/").status_code == 404
    inactive, _ = make_product(name="مخفي", category=CategoryFactory(is_active=False))
    assert api_client.get(f"{PRODUCTS}{inactive.slug}/").status_code == 404
    r = api_client.get(f"{PRODUCTS}nope/")
    assert r.status_code == 404 and r.json()["code"] == "not_found"


# --- BE-11: active_offer + query budget -------------------------------
def test_active_offer_is_best_live_percentage(api_client):
    spices = CategoryFactory(slug="spices")
    p, _ = make_product(name="كمون", category=spices)
    other, _ = make_product(name="تاني", category=CategoryFactory(slug="o"))
    percentage_offer(10, category=spices, name="عشرة")
    best = percentage_offer(20, products=[p], name="عشرين")
    percentage_offer(50, category=spices, name="منتهي", **expired())
    percentage_offer(60, category=spices, name="موقوف", is_active=False)
    results = {x["name"]: x for x in api_client.get(PRODUCTS).json()["results"]}
    assert results["كمون"]["active_offer"] == {
        "id": best.id, "name": "عشرين", "type": "percentage", "value": 20
    }  # fmt: skip
    assert results["تاني"]["active_offer"] is None
    detail = api_client.get(f"{PRODUCTS}{p.slug}/").json()
    assert detail["active_offer"]["id"] == best.id


@pytest.mark.parametrize("n", [1, 5, 20])
def test_products_list_query_budget_independent_of_page_size(api_client, n):
    cat = CategoryFactory(slug="spices")
    other = CategoryFactory(slug="herbs")
    products = []
    for i in range(n):
        p, v = make_product(name=f"م{i}", category=cat if i % 2 else other)
        VariantFactory(product=p, label="كيلو", is_default=False, price=200)
        products.append(p)
    percentage_offer(15, category=cat)
    percentage_offer(10, products=products[:3], name="منتجات")
    percentage_offer(5)
    with CaptureQueriesContext(connection) as ctx:
        r = api_client.get(PRODUCTS)
    assert r.status_code == 200 and len(r.json()["results"]) == n
    assert len(ctx) <= 4, [q["sql"] for q in ctx.captured_queries]

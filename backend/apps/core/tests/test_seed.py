from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Category, Product, ProductVariant
from apps.core.management.commands.seed_abo_samra import next_thursday_end
from apps.offers.models import Offer

pytestmark = pytest.mark.django_db


@pytest.fixture
def seeded(settings):
    settings.ADMIN_PHONE = "01000000000"
    settings.ADMIN_PASSWORD = "seed-pass-123"
    settings.ADMIN_NAME = "أبو سمرة"
    call_command("seed_abo_samra", verbosity=0)


def counts():
    return (
        Category.objects.count(),
        Product.objects.count(),
        ProductVariant.objects.count(),
        Offer.objects.count(),
        User.objects.count(),
    )


def test_seed_content(seeded):
    assert Category.objects.count() == 6
    assert Product.objects.count() == 16
    assert set(Product.objects.filter(is_featured=True).values_list("name", flat=True)) == {
        "كمون مطحون", "عسل نحل طبيعي", "كركديه", "لوز مقشر",
    }  # fmt: skip
    cumin = Product.objects.get(name="كمون مطحون")
    assert [(v.label, int(v.price)) for v in cumin.variants.all()] == [
        ("ربع كيلو", 60), ("نص كيلو", 115), ("كيلو", 220),
    ]  # fmt: skip
    for product in Product.objects.all():
        assert product.variants.filter(is_default=True).count() == 1
    assert Offer.objects.count() == 3
    bundle = Offer.objects.get(type="bundle")
    assert bundle.bundle_price == 160 and bundle.bundle_items.count() == 3
    assert {i.variant.label for i in bundle.bundle_items.all()} == {"ربع كيلو"}
    assert Offer.objects.get(type="free_delivery").min_order == 500
    pct = Offer.objects.get(type="percentage")
    assert pct.is_featured and pct.value == 15 and pct.target_category.slug == "spices"
    staff = User.objects.get(phone="01000000000")
    assert staff.is_staff and staff.check_password("seed-pass-123")


def test_seed_twice_creates_no_duplicates(seeded):
    before = counts()
    call_command("seed_abo_samra", verbosity=0)
    assert counts() == before


def test_seed_keeps_owner_edits(seeded):
    Product.objects.filter(name="كركم").update(description="تعديل")
    ProductVariant.objects.filter(product__name="كركم").update(price=99)
    call_command("seed_abo_samra", verbosity=0)
    assert ProductVariant.objects.get(product__name="كركم").price == 99


def test_seed_without_admin_env_skips_staff(settings, capsys):
    settings.ADMIN_PHONE = ""
    settings.ADMIN_PASSWORD = ""
    call_command("seed_abo_samra", verbosity=0)
    assert not User.objects.exists()


def test_seeded_catalog_and_reference_quote(seeded, api_client):
    assert api_client.get("/api/v1/products/").json()["count"] == 16
    active = api_client.get("/api/v1/offers/active/").json()
    assert len(active) == 3 and active[0]["is_featured"]
    bundle = next(o for o in active if o["type"] == "bundle")
    r = api_client.post(
        "/api/v1/cart/quote/", {"bundles": [{"offer_id": bundle["id"], "qty": 1}]}, format="json"
    )
    assert r.json()["subtotal"] == 160 and r.json()["warnings"] == []


def test_next_thursday_end():
    tz = ZoneInfo("Africa/Cairo")
    wed = timezone.make_aware(datetime(2026, 11, 4, 10, 0), tz)
    thu = timezone.make_aware(datetime(2026, 11, 5, 10, 0), tz)
    assert next_thursday_end(wed).strftime("%Y-%m-%d %H:%M") == "2026-11-05 23:59"
    assert next_thursday_end(thu).strftime("%Y-%m-%d %H:%M") == "2026-11-12 23:59"

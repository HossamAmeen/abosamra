from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.tests.factories import CategoryFactory, make_product
from apps.core.models import ShopSettings
from apps.offers.tests.factories import (
    bundle_offer,
    expired,
    free_delivery_offer,
    percentage_offer,
)
from apps.orders.services.pricing import quote

pytestmark = pytest.mark.django_db


def items(*pairs):
    return [{"variant_id": v.id, "qty": q} for v, q in pairs]


@pytest.fixture
def shop():
    return ShopSettings.load()  # 30 delivery, 500 threshold


@pytest.fixture
def spices():
    return CategoryFactory(slug="spices", name="بهارات")


@pytest.fixture
def honey_cat():
    return CategoryFactory(slug="honey", name="عسل وزيوت")


def test_reference_case(shop, spices, honey_cat):
    _, cumin = make_product("كمون مطحون", 60, spices)
    _, pepper = make_product("فلفل أسود حب", 95, spices)
    _, honey = make_product("عسل نحل طبيعي", 220, honey_cat, label="كيلو")
    offer = percentage_offer(15, category=spices, name="خصم 15% على كل البهارات")

    q = quote(items((cumin, 2), (pepper, 1), (honey, 1)), []).to_dict()

    assert q["subtotal"] == 435
    assert q["discount_total"] == 32  # 15% of 215 = 32.25
    assert q["discounts"] == [
        {"offer_id": offer.id, "label": "خصم 15% على كل البهارات", "amount": 32}
    ]
    assert q["delivery_fee"] == 30
    assert q["total"] == 433
    assert q["free_delivery_threshold"] == 500
    assert q["free_delivery_remaining"] == 97
    assert q["warnings"] == []
    assert q["lines"][0] == {
        "variant_id": cumin.id, "offer_id": None, "name": "كمون مطحون",
        "unit_label": "ربع كيلو", "qty": 2, "unit_price": 60, "line_total": 120,
    }  # fmt: skip


def test_best_percentage_wins_no_stacking(shop, spices):
    p, v = make_product("كمون", 100, spices)
    percentage_offer(10, category=spices, name="قسم")
    percentage_offer(15, products=[p], name="منتج")
    best = percentage_offer(20, name="الكل")
    q = quote(items((v, 1)), [])
    assert [d["offer_id"] for d in q.discounts] == [best.id]
    assert q.discount_total == 20


def test_discounts_grouped_per_offer(shop, spices, honey_cat):
    _, a = make_product("أ", 100, spices)
    _, b = make_product("ب", 50, spices)
    _, c = make_product("ج", 200, honey_cat)
    o1 = percentage_offer(10, category=spices, name="بهارات")
    o2 = percentage_offer(25, category=honey_cat, name="عسل")
    q = quote(items((a, 1), (b, 2), (c, 1)), [])
    amounts = {d["offer_id"]: d["amount"] for d in q.discounts}
    assert amounts == {o1.id: Decimal("20"), o2.id: Decimal("50")}
    assert q.discount_total == 70


def test_rounding_half_up(shop):
    _, v = make_product("صغير", 5)
    percentage_offer(10)  # 0.5 -> 1
    assert quote(items((v, 1)), []).discount_total == 1


def test_bundles_not_discounted_and_priced_at_bundle_price(shop, spices):
    _, v1 = make_product("ينسون", 50, spices)
    _, v2 = make_product("كركديه", 65, spices)
    bundle = bundle_offer([(v1, 1), (v2, 1)], price=100, name="باكدج الشتا")
    percentage_offer(50, name="الكل")
    q = quote([], [{"offer_id": bundle.id, "qty": 2}])
    assert q.subtotal == 200 and q.discount_total == 0 and q.discounts == []
    line = q.lines[0]
    assert (line.name, line.offer_id, line.variant_id, line.unit_price, line.qty) == (
        "باكدج الشتا", bundle.id, None, 100, 2
    )  # fmt: skip
    assert q.to_dict()["lines"][0]["variant_id"] is None


def test_bundle_with_regular_lines_discounts_only_regular(shop, spices):
    _, v1 = make_product("أ", 50, spices)
    _, v2 = make_product("ب", 65, spices)
    _, reg = make_product("ج", 100, spices)
    bundle = bundle_offer([(v1, 1), (v2, 1)], price=100)
    percentage_offer(10, category=spices)
    q = quote(items((reg, 1)), [{"offer_id": bundle.id, "qty": 1}])
    assert q.subtotal == 200 and q.discount_total == 10


@pytest.mark.parametrize(
    ("subtotal_price", "fee", "remaining"),
    [(499, 30, 1), (500, 0, 0), (501, 0, 0)],
)
def test_free_delivery_exactly_at_threshold(shop, subtotal_price, fee, remaining):
    _, v = make_product("x", subtotal_price)
    q = quote(items((v, 1)), [])
    assert q.delivery_fee == fee
    assert q.free_delivery_remaining == remaining
    assert q.total == subtotal_price + fee


def test_threshold_uses_after_discount_amount(shop, spices):
    _, v = make_product("x", 520, spices)
    percentage_offer(10, category=spices)  # 520 - 52 = 468 < 500
    q = quote(items((v, 1)), [])
    assert q.delivery_fee == 30 and q.free_delivery_remaining == 32


def test_free_delivery_offer_lowers_threshold(shop):
    free_delivery_offer(300)
    _, v = make_product("x", 300)
    q = quote(items((v, 1)), [])
    assert q.free_delivery_threshold == 300
    assert q.delivery_fee == 0 and q.free_delivery_remaining == 0


def test_free_delivery_offer_cannot_raise_threshold(shop):
    free_delivery_offer(900)
    _, v = make_product("x", 100)
    assert quote(items((v, 1)), []).free_delivery_threshold == 500


def test_expired_and_inactive_offers_ignored(shop, spices):
    _, v = make_product("x", 100, spices)
    percentage_offer(50, category=spices, **expired())
    percentage_offer(50, category=spices, is_active=False)
    percentage_offer(50, category=spices, starts_at=timezone.now() + timedelta(days=1))
    free_delivery_offer(10, **expired())
    q = quote(items((v, 1)), [])
    assert q.discount_total == 0 and q.free_delivery_threshold == 500 and q.delivery_fee == 30


def test_offer_ending_after_now_param_is_live(shop, spices):
    _, v = make_product("x", 100, spices)
    percentage_offer(10, category=spices, **expired())
    past = timezone.now() - timedelta(days=5)
    assert quote(items((v, 1)), [], now=past).discount_total == 10


def test_expired_bundle_warns_offer_expired(shop, spices):
    _, v1 = make_product("أ", 50)
    _, v2 = make_product("ب", 50)
    old = bundle_offer([(v1, 1), (v2, 1)], price=80, **expired())
    q = quote([], [{"offer_id": old.id, "qty": 1}, {"offer_id": 9999, "qty": 1}])
    assert q.lines == [] and q.subtotal == 0
    assert [(w["code"], w["offer_id"]) for w in q.warnings] == [
        ("offer_expired", old.id),
        ("offer_expired", 9999),
    ]


def test_non_bundle_offer_id_in_bundles_is_offer_expired(shop):
    o = percentage_offer(10)
    q = quote([], [{"offer_id": o.id, "qty": 1}])
    assert q.warnings[0]["code"] == "offer_expired"


def test_unavailable_not_found_and_hidden_category_warnings(shop):
    _, ok = make_product("متاح", 100)
    _, gone = make_product("خلصان", 100, is_available=False)
    _, archived = make_product("مؤرشف", 100, is_archived=True)
    _, hidden = make_product("قسم مخفي", 100, CategoryFactory(is_active=False))
    q = quote(
        items((ok, 1), (gone, 1), (archived, 1), (hidden, 1)) + [{"variant_id": 987654, "qty": 1}],
        [],
    )
    assert [ln.variant_id for ln in q.lines] == [ok.id]
    codes = {w["variant_id"]: w["code"] for w in q.warnings}
    assert codes == {
        gone.id: "unavailable",
        archived.id: "unavailable",
        hidden.id: "unavailable",
        987654: "not_found",
    }
    assert all(w["detail"] for w in q.warnings)
    assert q.subtotal == 100


def test_insufficient_stock_uses_stock_factor_and_cumulative_lines(shop):
    p, quarter = make_product("كمون", 60, stock_qty=Decimal("1"))
    quarter.stock_factor = Decimal("0.25")
    quarter.save()
    from apps.catalog.tests.factories import VariantFactory

    kilo = VariantFactory(
        product=p, label="كيلو", price=220, stock_factor=Decimal("1"), is_default=False
    )
    assert not quote(items((quarter, 4)), []).warnings  # exactly 1 kg
    q = quote(items((quarter, 5)), [])
    assert q.warnings[0]["code"] == "insufficient_stock" and q.lines == []
    # two lines of the same product draw from the same stock
    q = quote(items((quarter, 2), (kilo, 1)), [])
    assert [ln.variant_id for ln in q.lines] == [quarter.id]
    assert q.warnings[0]["variant_id"] == kilo.id


def test_untracked_stock_never_insufficient(shop):
    _, v = make_product("x", 10, stock_qty=None)
    assert not quote(items((v, 50)), []).warnings


def test_duplicate_variant_rows_are_merged(shop):
    _, v = make_product("x", 10)
    q = quote([{"variant_id": v.id, "qty": 2}, {"variant_id": v.id, "qty": 3}], [])
    assert len(q.lines) == 1 and q.lines[0].qty == 5


def test_bundle_items_checked_for_stock_and_availability(shop):
    p1, v1 = make_product("أ", 50, stock_qty=Decimal("1"))
    _, v2 = make_product("ب", 50)
    b = bundle_offer([(v1, 1), (v2, 1)], price=80)
    ok = quote([], [{"offer_id": b.id, "qty": 1}])
    assert len(ok.lines) == 1 and not ok.warnings
    bad = quote([], [{"offer_id": b.id, "qty": 2}])
    assert bad.lines == []
    assert bad.warnings[0]["code"] == "insufficient_stock"
    assert bad.warnings[0]["variant_id"] == v1.id and bad.warnings[0]["offer_id"] == b.id
    v2.product.is_available = False
    v2.product.save()
    assert quote([], [{"offer_id": b.id, "qty": 1}]).warnings[0]["code"] == "unavailable"


def test_bundle_and_regular_line_share_stock(shop):
    _, v1 = make_product("أ", 50, stock_qty=Decimal("2"))
    _, v2 = make_product("ب", 50)
    b = bundle_offer([(v1, 1), (v2, 1)], price=80)
    q = quote(items((v1, 2)), [{"offer_id": b.id, "qty": 1}])
    assert [ln.variant_id for ln in q.lines] == [v1.id]
    assert q.warnings[0]["code"] == "insufficient_stock"


def test_empty_cart(shop):
    q = quote([], []).to_dict()
    assert q["lines"] == [] and q["subtotal"] == 0 and q["total"] == 0
    assert q["delivery_fee"] == 0 and q["free_delivery_remaining"] == 500


def test_uses_shop_settings_values(shop):
    shop.delivery_fee = Decimal("45")
    shop.free_delivery_threshold = Decimal("200")
    shop.save()
    _, v = make_product("x", 100)
    q = quote(items((v, 1)), [])
    assert (q.delivery_fee, q.free_delivery_remaining, q.total) == (45, 100, 145)


def test_for_update_flag_runs_inside_transaction(shop):
    from django.db import transaction

    _, v = make_product("x", 100)
    with transaction.atomic():
        q = quote(items((v, 1)), [], for_update=True)
    assert q.subtotal == 100

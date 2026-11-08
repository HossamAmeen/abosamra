import pytest

from apps.catalog.tests.factories import CategoryFactory, make_product
from apps.offers.tests.factories import bundle_offer, percentage_offer

pytestmark = pytest.mark.django_db

QUOTE = "/api/v1/cart/quote/"


def test_guest_can_quote_reference_case(api_client):
    spices = CategoryFactory(slug="spices")
    honey = CategoryFactory(slug="honey")
    _, cumin = make_product("كمون مطحون", 60, spices)
    _, pepper = make_product("فلفل أسود حب", 95, spices)
    _, honey_v = make_product("عسل نحل طبيعي", 220, honey, label="كيلو")
    percentage_offer(15, category=spices, name="خصم 15% على كل البهارات")
    r = api_client.post(
        QUOTE,
        {
            "items": [
                {"variant_id": cumin.id, "qty": 2},
                {"variant_id": pepper.id, "qty": 1},
                {"variant_id": honey_v.id, "qty": 1},
            ],
            "bundles": [],
        },
        format="json",
    )
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {
        "lines", "subtotal", "discounts", "discount_total", "delivery_fee",
        "free_delivery_threshold", "free_delivery_remaining", "total", "warnings",
    }  # fmt: skip
    assert (body["subtotal"], body["discount_total"], body["delivery_fee"]) == (435, 32, 30)
    assert (body["total"], body["free_delivery_remaining"]) == (433, 97)


def test_authenticated_and_bundles(auth_client):
    _, v1 = make_product("أ", 50)
    _, v2 = make_product("ب", 50)
    b = bundle_offer([(v1, 1), (v2, 1)], price=80)
    r = auth_client.post(QUOTE, {"bundles": [{"offer_id": b.id, "qty": 2}]}, format="json")
    assert r.status_code == 200 and r.json()["subtotal"] == 160


def test_warnings_returned_in_body(api_client):
    r = api_client.post(QUOTE, {"items": [{"variant_id": 424242, "qty": 1}]}, format="json")
    assert r.status_code == 200
    assert r.json()["warnings"][0]["code"] == "not_found"


def test_empty_body_ok(api_client):
    r = api_client.post(QUOTE, {}, format="json")
    assert r.status_code == 200 and r.json()["lines"] == []


@pytest.mark.parametrize("qty", [0, 51, -1, "x", None, 1.5])
def test_qty_must_be_int_1_to_50(api_client, qty):
    _, v = make_product("x", 10)
    r = api_client.post(QUOTE, {"items": [{"variant_id": v.id, "qty": qty}]}, format="json")
    assert r.status_code == 400
    assert "qty" in r.json()["items"][0]


def test_qty_bounds_accepted(api_client):
    _, v = make_product("x", 10)
    for qty in (1, 50):
        r = api_client.post(QUOTE, {"items": [{"variant_id": v.id, "qty": qty}]}, format="json")
        assert r.status_code == 200 and r.json()["lines"][0]["qty"] == qty


def test_bundle_qty_validated(api_client):
    r = api_client.post(QUOTE, {"bundles": [{"offer_id": 1, "qty": 51}]}, format="json")
    assert r.status_code == 400 and "qty" in r.json()["bundles"][0]


def test_qty_error_message_is_arabic(api_client):
    r = api_client.post(QUOTE, {"items": [{"variant_id": 1, "qty": 0}]}, format="json")
    assert r.json()["items"][0]["qty"] == ["الكمية لازم تكون من 1 لـ 50"]


def test_missing_variant_id_is_400(api_client):
    r = api_client.post(QUOTE, {"items": [{"qty": 1}]}, format="json")
    assert r.status_code == 400


def test_quote_throttle_scope(api_client, set_rate):
    set_rate("quote", "2/minute")
    for _ in range(2):
        assert api_client.post(QUOTE, {}, format="json").status_code == 200
    r = api_client.post(QUOTE, {}, format="json")
    assert r.status_code == 429
    assert r.json()["code"] == "throttled"
    assert set(r.json()) == {"detail", "code"}


def test_get_not_allowed(api_client):
    assert api_client.get(QUOTE).status_code == 405

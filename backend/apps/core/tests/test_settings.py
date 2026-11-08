import pytest

from apps.core.models import ShopSettings

pytestmark = pytest.mark.django_db


def test_settings_endpoint_shape_and_defaults(api_client):
    r = api_client.get("/api/v1/settings/")
    assert r.status_code == 200
    assert r.json() == {
        "shop_name": "أبو سمرة",
        "phone": "",
        "whatsapp": "",
        "delivery_fee": 30,
        "free_delivery_threshold": 500,
        "currency": "EGP",
        "is_accepting_orders": True,
    }


def test_singleton_load_is_get_or_create_pk1():
    assert ShopSettings.objects.count() == 0
    a = ShopSettings.load()
    b = ShopSettings.load()
    assert a.pk == b.pk == 1
    assert ShopSettings.objects.count() == 1


def test_saving_new_instance_never_creates_second_row():
    ShopSettings.load()
    ShopSettings(shop_name="تاني").save()
    assert ShopSettings.objects.count() == 1
    assert ShopSettings.load().shop_name == "تاني"


def test_singleton_cannot_be_deleted():
    obj = ShopSettings.load()
    obj.delete()
    assert ShopSettings.objects.filter(pk=1).exists()


def test_endpoint_reflects_changes(api_client):
    s = ShopSettings.load()
    s.is_accepting_orders = False
    s.delivery_fee = 45
    s.save()
    body = api_client.get("/api/v1/settings/").json()
    assert body["is_accepting_orders"] is False
    assert body["delivery_fee"] == 45

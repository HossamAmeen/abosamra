import pytest

from apps.accounts.models import User

URL = "/api/v1/admin/staff/"
ADMIN_LOGIN = "/api/v1/auth/admin/login/"

pytestmark = pytest.mark.django_db


def test_list_returns_only_active_staff(admin_client, staff, customer):
    User.objects.create_superuser(phone="01212345678", name="قديم", password="x-pass-123")
    User.objects.filter(phone="01212345678").update(is_active=False)
    r = admin_client.get(URL)
    assert r.status_code == 200
    rows = r.json()["results"]
    assert [u["phone"] for u in rows] == [staff.phone]
    assert "password" not in rows[0]


def test_create_staff_can_log_in(admin_client, api_client):
    r = admin_client.post(
        URL, {"name": "محمود", "phone": "+20 122 000 1111", "password": "strong-pass-1"}
    )
    assert r.status_code == 201, r.json()
    body = r.json()
    assert body["phone"] == "01220001111" and "password" not in body
    user = User.objects.get(phone="01220001111")
    assert user.is_staff and user.is_superuser
    login = api_client.post(ADMIN_LOGIN, {"phone": "01220001111", "password": "strong-pass-1"})
    assert login.status_code == 200
    assert login.json()["user"]["is_staff"] is True


@pytest.mark.parametrize("phone_attr", ["staff", "customer"])
def test_create_existing_phone_409(request, admin_client, phone_attr):
    phone = request.getfixturevalue(phone_attr).phone
    r = admin_client.post(URL, {"name": "تاني", "phone": phone, "password": "strong-pass-1"})
    assert r.status_code == 409
    assert r.json()["code"] == "phone_exists"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"name": "م", "phone": "01220001111", "password": "strong-pass-1"}, "name"),
        ({"name": "محمود", "phone": "123", "password": "strong-pass-1"}, "phone"),
        ({"name": "محمود", "phone": "01220001111", "password": "short"}, "password"),
        ({"name": "محمود", "phone": "01220001111", "password": "12345678"}, "password"),
    ],
)
def test_create_validation(admin_client, payload, field):
    r = admin_client.post(URL, payload)
    assert r.status_code == 400
    assert field in r.json()
    assert not User.objects.filter(phone="01220001111").exists()


def test_customer_cannot_create_staff(auth_client):
    r = auth_client.post(URL, {"name": "هاكر", "phone": "01220001111", "password": "strong-pass-1"})
    assert r.status_code == 403
    assert not User.objects.filter(phone="01220001111").exists()


PASSWORD_URL = "/api/v1/admin/me/password/"


def test_change_password(admin_client, api_client, staff):
    r = admin_client.post(
        PASSWORD_URL, {"current_password": "s3cret-pass", "new_password": "brand-new-pass"}
    )
    assert r.status_code == 204
    staff.refresh_from_db()
    assert staff.check_password("brand-new-pass")
    old = api_client.post(ADMIN_LOGIN, {"phone": staff.phone, "password": "s3cret-pass"})
    assert old.status_code == 401


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"current_password": "wrong-pass", "new_password": "brand-new-pass"}, "current_password"),
        ({"current_password": "s3cret-pass", "new_password": "short"}, "new_password"),
        ({"current_password": "s3cret-pass", "new_password": "123456789"}, "new_password"),
        ({"current_password": "s3cret-pass", "new_password": "s3cret-pass"}, "new_password"),
        ({"new_password": "brand-new-pass"}, "current_password"),
    ],
)
def test_change_password_validation(admin_client, staff, payload, field):
    r = admin_client.post(PASSWORD_URL, payload)
    assert r.status_code == 400
    assert field in r.json()
    staff.refresh_from_db()
    assert staff.check_password("s3cret-pass")


def test_customer_cannot_change_password_here(auth_client):
    r = auth_client.post(PASSWORD_URL, {"current_password": "x", "new_password": "brand-new-pass"})
    assert r.status_code == 403

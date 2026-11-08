from datetime import UTC, datetime

import pytest
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.accounts.tokens import AppRefreshToken

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/auth/register/"
LOGIN = "/api/v1/auth/login/"
ADMIN_LOGIN = "/api/v1/auth/admin/login/"
REFRESH = "/api/v1/auth/token/refresh/"
LOGOUT = "/api/v1/auth/logout/"
ME = "/api/v1/me/"

BAD_PHONE_MSG = "اكتب رقم موبايل مصري صحيح (11 رقم يبدأ بـ 01)"


def days_left(token_str):
    exp = datetime.fromtimestamp(AppRefreshToken(token_str)["exp"], tz=UTC)
    return (exp - datetime.now(tz=UTC)).total_seconds() / 86400


# --- register ---------------------------------------------------------
def test_register_creates_customer_and_returns_tokens(api_client):
    r = api_client.post(REGISTER, {"name": "منى", "phone": "٠١٠١٢٣٤٥٦٧٨", "email": "m@x.com"})
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"access", "refresh", "user"}
    assert body["user"]["phone"] == "01012345678"
    assert body["user"]["is_staff"] is False
    user = User.objects.get(phone="01012345678")
    assert not user.has_usable_password()


def test_register_email_optional(api_client):
    r = api_client.post(REGISTER, {"name": "منى", "phone": "01012345678"})
    assert r.status_code == 201
    assert r.json()["user"]["email"] == ""


def test_register_duplicate_phone_409(api_client, customer):
    r = api_client.post(REGISTER, {"name": "تاني", "phone": "+201012345678"})
    assert r.status_code == 409
    assert r.json() == {"detail": "الرقم ده عنده حساب، ادخل بيه", "code": "phone_exists"}


def test_register_invalid_phone_400_exact_message(api_client):
    r = api_client.post(REGISTER, {"name": "منى", "phone": "0101234567"})
    assert r.status_code == 400
    assert r.json() == {"phone": [BAD_PHONE_MSG]}


@pytest.mark.parametrize(
    "payload,field",
    [
        ({"name": "م", "phone": "01012345678"}, "name"),
        ({"name": "م" * 81, "phone": "01012345678"}, "name"),
        ({"phone": "01012345678"}, "name"),
        ({"name": "منى"}, "phone"),
        ({"name": "منى", "phone": "01012345678", "email": "nope"}, "email"),
    ],
)
def test_register_validation_errors(api_client, payload, field):
    r = api_client.post(REGISTER, payload)
    assert r.status_code == 400
    assert field in r.json()


# --- customer login ---------------------------------------------------
def test_login_existing_customer(api_client, customer):
    r = api_client.post(LOGIN, {"phone": "٠١٠١٢٣٤٥٦٧٨"})
    assert r.status_code == 200
    assert r.json()["user"]["id"] == customer.id


def test_login_unknown_phone_404(api_client):
    r = api_client.post(LOGIN, {"phone": "01099999999"})
    assert r.status_code == 404
    assert r.json() == {"detail": "مفيش حساب بالرقم ده", "code": "not_found"}


def test_login_staff_phone_is_404(api_client, staff):
    r = api_client.post(LOGIN, {"phone": staff.phone})
    assert r.status_code == 404
    assert r.json()["code"] == "not_found"


def test_login_inactive_customer_404(api_client, customer):
    customer.is_active = False
    customer.save()
    assert api_client.post(LOGIN, {"phone": customer.phone}).status_code == 404


def test_login_invalid_phone_400(api_client):
    r = api_client.post(LOGIN, {"phone": "12"})
    assert r.status_code == 400
    assert r.json() == {"phone": [BAD_PHONE_MSG]}


# --- admin login ------------------------------------------------------
def test_admin_login_ok(api_client, staff):
    r = api_client.post(ADMIN_LOGIN, {"phone": staff.phone, "password": "s3cret-pass"})
    assert r.status_code == 200
    assert r.json()["user"]["is_staff"] is True


@pytest.mark.parametrize("password", ["wrong", ""])
def test_admin_login_wrong_password_401(api_client, staff, password):
    r = api_client.post(ADMIN_LOGIN, {"phone": staff.phone, "password": password})
    assert r.status_code == 401
    assert r.json()["detail"] == "الرقم أو الباسورد غلط"


def test_admin_login_customer_rejected(api_client, customer):
    r = api_client.post(ADMIN_LOGIN, {"phone": customer.phone, "password": "anything"})
    assert r.status_code == 401
    assert r.json()["detail"] == "الرقم أو الباسورد غلط"


def test_admin_login_garbage_phone_401(api_client):
    r = api_client.post(ADMIN_LOGIN, {"phone": "zzz", "password": "x"})
    assert r.status_code == 401


def test_admin_login_inactive_staff_401(api_client, staff):
    staff.is_active = False
    staff.save()
    r = api_client.post(ADMIN_LOGIN, {"phone": staff.phone, "password": "s3cret-pass"})
    assert r.status_code == 401


# --- JWT claims & lifetimes ------------------------------------------
def test_claims_and_lifetimes_customer(api_client, customer):
    body = api_client.post(LOGIN, {"phone": customer.phone}).json()
    access = AccessToken(body["access"])
    assert access["name"] == customer.name
    assert access["is_staff"] is False
    assert 29 <= (access["exp"] - access["iat"]) / 60 <= 30
    assert 59.9 < days_left(body["refresh"]) <= 60


def test_lifetimes_staff(api_client, staff):
    body = api_client.post(ADMIN_LOGIN, {"phone": staff.phone, "password": "s3cret-pass"}).json()
    assert AccessToken(body["access"])["is_staff"] is True
    assert 6.9 < days_left(body["refresh"]) <= 7


# --- refresh / logout -------------------------------------------------
def test_refresh_rotates_and_blacklists_old(api_client, customer):
    old = api_client.post(LOGIN, {"phone": customer.phone}).json()["refresh"]
    r = api_client.post(REFRESH, {"refresh": old})
    assert r.status_code == 200
    assert set(r.json()) == {"access", "refresh"}
    assert r.json()["refresh"] != old
    assert BlacklistedToken.objects.count() == 1
    reuse = api_client.post(REFRESH, {"refresh": old})
    assert reuse.status_code == 401
    assert reuse.json()["code"] == "token_not_valid"


def test_refresh_keeps_staff_lifetime_after_rotation(api_client, staff):
    old = api_client.post(ADMIN_LOGIN, {"phone": staff.phone, "password": "s3cret-pass"}).json()[
        "refresh"
    ]
    new = api_client.post(REFRESH, {"refresh": old}).json()["refresh"]
    assert days_left(new) <= 7


def test_refresh_garbage_401_common_format(api_client):
    r = api_client.post(REFRESH, {"refresh": "garbage"})
    assert r.status_code == 401
    assert set(r.json()) == {"detail", "code"}


def test_logout_blacklists_and_returns_204(api_client, customer):
    refresh = api_client.post(LOGIN, {"phone": customer.phone}).json()["refresh"]
    r = api_client.post(LOGOUT, {"refresh": refresh})
    assert r.status_code == 204
    assert api_client.post(REFRESH, {"refresh": refresh}).status_code == 401


def test_logout_invalid_token_401(api_client):
    r = api_client.post(LOGOUT, {"refresh": "nope"})
    assert r.status_code == 401
    assert r.json()["code"] == "token_not_valid"


def test_logout_requires_refresh_field(api_client):
    assert api_client.post(LOGOUT, {}).status_code == 400


# --- /me/ -------------------------------------------------------------
def test_me_requires_auth(api_client):
    r = api_client.get(ME)
    assert r.status_code == 401
    assert r.json()["code"] == "not_authenticated"


def test_me_get(auth_client, customer):
    r = auth_client.get(ME)
    assert r.status_code == 200
    assert r.json() == {
        "id": customer.id,
        "name": "أحمد",
        "phone": "01012345678",
        "email": "a@example.com",
        "default_address": "",
        "area": "",
        "is_staff": False,
    }


def test_me_patch_updates_allowed_fields_only(auth_client, customer):
    r = auth_client.patch(
        ME,
        {
            "name": "اسم جديد",
            "email": "n@x.com",
            "default_address": "١٢ شارع التحرير القاهرة",
            "area": "الدقي",
            "phone": "01099999999",
            "is_staff": True,
        },
    )
    assert r.status_code == 200
    customer.refresh_from_db()
    assert customer.name == "اسم جديد"
    assert customer.area == "الدقي"
    assert customer.phone == "01012345678"
    assert customer.is_staff is False


def test_me_patch_validation(auth_client):
    r = auth_client.patch(ME, {"name": "م"})
    assert r.status_code == 400
    assert "name" in r.json()


def test_me_put_not_allowed(auth_client):
    assert auth_client.put(ME, {}).status_code == 405


def test_me_with_bad_token_401(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer junk")
    r = api_client.get(ME)
    assert r.status_code == 401
    assert r.json()["code"] == "token_not_valid"

import pytest
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from common import messages
from common.throttling import (
    AuthRateThrottle,
    OrdersRateThrottle,
    QuoteRateThrottle,
    SensitiveRateThrottle,
)

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/auth/register/"
LOGIN = "/api/v1/auth/login/"
ADMIN_LOGIN = "/api/v1/auth/admin/login/"


def view_with(throttle, user=None):
    class V(APIView):
        authentication_classes: list = []
        permission_classes = [AllowAny]
        throttle_classes = [throttle]

        def get(self, request):
            return Response({"ok": True})

    return V.as_view()


def hit(view, n, user=None, ip="1.1.1.1"):
    codes = []
    for _ in range(n):
        request = APIRequestFactory().get("/x/", REMOTE_ADDR=ip)
        if user:
            from rest_framework.test import force_authenticate

            force_authenticate(request, user=user)
        codes.append(view(request).status_code)
    return codes


def test_api_allows_requests_within_rate_limit(api_client, set_rate):
    set_rate("auth", "3/minute")
    codes = [api_client.post(LOGIN, {"phone": "01099999999"}).status_code for _ in range(3)]
    assert codes == [404, 404, 404]


@pytest.mark.parametrize("url", [REGISTER, LOGIN, ADMIN_LOGIN])
def test_auth_endpoint_uses_stricter_throttle(api_client, set_rate, url):
    set_rate("auth", "2/minute")
    codes = [api_client.post(url, {"phone": "01099999999"}).status_code for _ in range(3)]
    assert codes[-1] == 429
    assert 429 not in codes[:2]


def test_api_rejects_requests_after_rate_limit_in_common_format(api_client, set_rate):
    set_rate("auth", "1/minute")
    api_client.post(LOGIN, {"phone": "01099999999"})
    r = api_client.post(LOGIN, {"phone": "01099999999"})
    assert r.status_code == 429
    assert r.json() == {"detail": messages.THROTTLED, "code": "throttled"}
    assert "Retry-After" in r


def test_auth_throttle_is_per_ip(api_client, set_rate):
    set_rate("auth", "1/minute")
    one = api_client.post(LOGIN, {"phone": "01099999999"}, REMOTE_ADDR="9.9.9.1")
    other = api_client.post(LOGIN, {"phone": "01099999999"}, REMOTE_ADDR="9.9.9.2")
    assert one.status_code == 404 and other.status_code == 404


def test_quote_scope_rate(set_rate):
    set_rate("quote", "2/minute")
    assert hit(view_with(QuoteRateThrottle), 3) == [200, 200, 429]


def test_orders_scope_is_per_user(set_rate, db):
    from apps.accounts.models import User

    a = User.objects.create_user("01012345678", "A")
    b = User.objects.create_user("01112345678", "B")
    set_rate("orders", "2/minute")
    view = view_with(OrdersRateThrottle)
    assert hit(view, 3, user=a) == [200, 200, 429]
    assert hit(view, 1, user=b) == [200]  # same IP, different user


def test_sensitive_endpoint_has_stricter_rate_limit(set_rate):
    set_rate("sensitive", "1/minute")
    assert hit(view_with(SensitiveRateThrottle), 2) == [200, 429]


def test_anonymous_user_uses_anonymous_throttle(set_rate, api_client):
    from rest_framework.throttling import AnonRateThrottle

    set_rate("anon", "1/minute")
    assert hit(view_with(AnonRateThrottle), 2) == [200, 429]


def test_authenticated_user_uses_user_throttle(set_rate, db):
    from rest_framework.throttling import UserRateThrottle

    from apps.accounts.models import User

    u = User.objects.create_user("01012345678", "A")
    set_rate("user", "1/minute")
    assert hit(view_with(UserRateThrottle), 2, user=u) == [200, 429]


def test_rates_come_from_settings():
    from django.conf import settings

    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    assert {"anon", "user", "auth", "quote", "orders", "sensitive", "health"} <= set(rates)
    assert AuthRateThrottle.scope == "auth"

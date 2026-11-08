import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from apps.accounts.models import User


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer(db):
    return User.objects.create_user(phone="01012345678", name="أحمد", email="a@example.com")


@pytest.fixture
def staff(db):
    return User.objects.create_superuser(phone="01112345678", name="الأدمن", password="s3cret-pass")


@pytest.fixture
def auth_client(api_client, customer):
    from apps.accounts.tokens import issue_tokens

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(customer)['access']}")
    return api_client


@pytest.fixture
def admin_client(staff):
    """Independent client authenticated as staff."""
    from apps.accounts.tokens import issue_tokens

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(staff)['access']}")
    return client


@pytest.fixture
def set_rate():
    """Lower a throttle scope's rate for one test (restored afterwards)."""
    original = dict(SimpleRateThrottle.THROTTLE_RATES)

    def _set(scope, rate):
        SimpleRateThrottle.THROTTLE_RATES[scope] = rate

    yield _set
    SimpleRateThrottle.THROTTLE_RATES.clear()
    SimpleRateThrottle.THROTTLE_RATES.update(original)

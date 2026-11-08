from unittest.mock import patch

import pytest
from django.conf import settings

URL = "/api/health/"
HEADER = {"HTTP_X_HEALTH_CHECK_TOKEN": "test-health-password"}


@pytest.mark.django_db
def test_health_endpoint_returns_success_with_valid_password(api_client):
    r = api_client.get(URL, **HEADER)
    assert r.status_code == 200
    assert r.json() == {"status": "healthy", "database": "ok"}


@pytest.mark.django_db
def test_health_endpoint_accepts_query_password(api_client):
    assert api_client.get(URL, {"password": "test-health-password"}).status_code == 200


def test_health_endpoint_rejects_invalid_password(api_client):
    r = api_client.get(URL, {"password": "wrong"})
    assert r.status_code == 403
    assert r.json()["code"] == "invalid_health_password"


def test_health_endpoint_requires_password(api_client):
    r = api_client.get(URL)
    assert r.status_code == 403
    assert r.json()["code"] == "health_password_required"


def test_health_endpoint_rejects_when_no_password_configured(api_client, settings):
    settings.HEALTH_CHECK_PASSWORD = ""
    assert api_client.get(URL, {"password": ""}).status_code == 403
    assert api_client.get(URL, {"password": "x"}).status_code == 403


@pytest.mark.django_db
def test_health_endpoint_does_not_expose_secret(api_client):
    for r in (api_client.get(URL, **HEADER), api_client.get(URL, {"password": "wrong"})):
        assert settings.HEALTH_CHECK_PASSWORD not in r.content.decode()
        assert settings.SECRET_KEY not in r.content.decode()


def test_health_reports_db_failure_without_leaking(api_client):
    with patch("apps.core.views.connection") as conn:
        conn.cursor.side_effect = Exception("password=hunter2 host=db")
        r = api_client.get(URL, **HEADER)
    assert r.status_code == 503
    assert r.json()["code"] == "db_unavailable"
    assert "hunter2" not in r.content.decode()


@pytest.mark.django_db
def test_health_has_own_throttle_scope(api_client, set_rate):
    set_rate("health", "2/minute")
    codes = [api_client.get(URL, **HEADER).status_code for _ in range(3)]
    assert codes == [200, 200, 429]

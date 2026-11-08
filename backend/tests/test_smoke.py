from django.conf import settings


def test_settings_locale():
    assert settings.LANGUAGE_CODE == "ar"
    assert settings.TIME_ZONE == "Africa/Cairo"
    assert settings.USE_TZ is True
    assert settings.AUTH_USER_MODEL == "accounts.User"


def test_unknown_url_returns_json_404(client):
    response = client.get("/nope/")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"

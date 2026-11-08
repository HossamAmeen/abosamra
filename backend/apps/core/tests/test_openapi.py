import pytest


@pytest.mark.django_db
def test_schema_served(api_client):
    r = api_client.get("/api/schema/")
    assert r.status_code == 200
    assert b"/api/v1/auth/register/" in r.content


def test_docs_and_redoc_served(api_client):
    assert api_client.get("/api/docs/").status_code == 200
    assert api_client.get("/api/redoc/").status_code == 200

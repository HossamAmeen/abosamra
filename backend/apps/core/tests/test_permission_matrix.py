"""QA-05: permission matrix (anonymous / customer / staff) over every route in openapi.yaml.

PA_CHECKLIST rows verified: B7.2, A6.1 (and B2.6/B7.1 indirectly).
"""

from pathlib import Path

import pytest
import yaml
from rest_framework.test import APIClient

from apps.accounts.tokens import issue_tokens

pytestmark = pytest.mark.django_db

OPENAPI = Path(__file__).resolve().parents[3] / "openapi.yaml"

# access levels: public = anyone, user = any authenticated account, staff = is_staff only
PUBLIC, USER, STAFF = "public", "user", "staff"
MATRIX = {
    ("get", "/api/v1/settings/"): PUBLIC,
    ("get", "/api/v1/categories/"): PUBLIC,
    ("get", "/api/v1/products/"): PUBLIC,
    ("get", "/api/v1/products/{slug}/"): PUBLIC,
    ("get", "/api/v1/offers/active/"): PUBLIC,
    ("post", "/api/v1/cart/quote/"): PUBLIC,
    ("post", "/api/v1/auth/register/"): PUBLIC,
    ("post", "/api/v1/auth/login/"): PUBLIC,
    ("post", "/api/v1/auth/admin/login/"): PUBLIC,
    ("post", "/api/v1/auth/token/refresh/"): PUBLIC,
    ("post", "/api/v1/auth/logout/"): PUBLIC,
    ("get", "/api/v1/me/"): USER,
    ("patch", "/api/v1/me/"): USER,
    ("post", "/api/v1/orders/"): USER,
    ("get", "/api/v1/orders/mine/"): USER,
    ("get", "/api/v1/orders/{id}/"): USER,
    ("get", "/api/v1/admin/dashboard/"): STAFF,
    ("get", "/api/v1/admin/orders/"): STAFF,
    ("get", "/api/v1/admin/orders/counts/"): STAFF,
    ("get", "/api/v1/admin/orders/{id}/"): STAFF,
    ("patch", "/api/v1/admin/orders/{id}/"): STAFF,
    ("get", "/api/v1/admin/products/"): STAFF,
    ("post", "/api/v1/admin/products/"): STAFF,
    ("get", "/api/v1/admin/products/{id}/"): STAFF,
    ("patch", "/api/v1/admin/products/{id}/"): STAFF,
    ("delete", "/api/v1/admin/products/{id}/"): STAFF,
    ("get", "/api/v1/admin/offers/"): STAFF,
    ("post", "/api/v1/admin/offers/"): STAFF,
    ("get", "/api/v1/admin/offers/{id}/"): STAFF,
    ("patch", "/api/v1/admin/offers/{id}/"): STAFF,
    ("delete", "/api/v1/admin/offers/{id}/"): STAFF,
    ("get", "/api/v1/admin/customers/"): STAFF,
    ("get", "/api/v1/admin/customers/{id}/orders/"): STAFF,
}
# Methods the spec file lists but that are not part of the access contract above (e.g. PUT aliases).
IGNORED_METHODS = {"put", "head", "options", "parameters"}
# Health is token-protected, covered in test_health.py.
SKIP_PATHS = {"/api/health/"}


def spec_operations():
    spec = yaml.safe_load(OPENAPI.read_text())
    return {
        (method, path)
        for path, item in spec["paths"].items()
        if path not in SKIP_PATHS
        for method in item
        if method not in IGNORED_METHODS
    }


def test_matrix_covers_every_openapi_operation():
    """A new route in openapi.yaml must be added to the matrix (and given an access level)."""
    ops = spec_operations()
    assert ops - set(MATRIX) == set(), "routes missing from the permission matrix"
    assert set(MATRIX) - ops == set(), "matrix lists routes that are not in openapi.yaml"


@pytest.fixture
def clients(customer, staff):
    def make(user):
        c = APIClient()
        if user:
            c.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user)['access']}")
        return c

    return {"anon": make(None), "customer": make(customer), "staff": make(staff)}


def call(client, method, path):
    url = path.replace("{slug}", "no-such-slug").replace("{id}", "999999")
    return getattr(client, method)(url, {}, format="json")


ROLES = ("anon", "customer", "staff")


def expected_allowed(level, role):
    return {
        PUBLIC: {"anon", "customer", "staff"},
        USER: {"customer", "staff"},
        STAFF: {"staff"},
    }[level] >= {role}


@pytest.mark.parametrize(("method", "path"), sorted(MATRIX), ids=lambda v: v)
@pytest.mark.parametrize("role", ROLES)
def test_permission_matrix(clients, method, path, role):
    level = MATRIX[(method, path)]
    r = call(clients[role], method, path)
    body = r.json() if r.content else {}
    if expected_allowed(level, role):
        # Allowed: the request reaches the view (any status except an auth rejection on the
        # protected levels; public endpoints may legitimately 401 on bad credentials/tokens).
        assert r.status_code != 403, (method, path, role, body)
        if level != PUBLIC:
            assert r.status_code != 401, (method, path, role, body)
        assert r.status_code < 500
    else:
        expected = 401 if role == "anon" else 403
        assert r.status_code == expected, (method, path, role, r.status_code, body)
        assert set(body) == {"detail", "code"}, body
        assert isinstance(body["detail"], str) and body["detail"]

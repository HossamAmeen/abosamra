import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import serializers, status
from rest_framework.exceptions import MethodNotAllowed, NotAuthenticated, Throttled
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from common import messages
from common.exceptions import ApiError
from common.pagination import StandardPagination


def make_view(exc):
    class V(APIView):
        authentication_classes = [JWTAuthentication]
        permission_classes = [AllowAny]
        throttle_classes: list = []

        def get(self, request):
            raise exc

    return V.as_view()


def call(exc):
    return make_view(exc)(APIRequestFactory().get("/x/"))


def test_401_not_authenticated():
    r = call(NotAuthenticated())
    assert r.status_code == 401
    assert r.data == {"detail": messages.NOT_AUTHENTICATED, "code": "not_authenticated"}


def test_403_permission_denied():
    r = call(PermissionDenied())
    assert r.status_code == 403
    assert r.data == {"detail": messages.PERMISSION_DENIED, "code": "permission_denied"}


@pytest.mark.parametrize("exc", [Http404(), Http404("x")])
def test_404_not_found(exc):
    r = call(exc)
    assert r.status_code == 404
    assert r.data == {"detail": messages.NOT_FOUND, "code": "not_found"}


def test_405_method_not_allowed():
    r = call(MethodNotAllowed("GET"))
    assert r.status_code == 405
    assert r.data["code"] == "method_not_allowed"


def test_429_throttled_keeps_retry_after():
    r = call(Throttled(wait=30))
    assert r.status_code == 429
    assert r.data == {"detail": messages.THROTTLED, "code": "throttled"}
    assert r["Retry-After"] == "30"


def test_500_unhandled_hides_internals():
    r = call(RuntimeError("secret internals"))
    assert r.status_code == 500
    assert r.data == {"detail": messages.SERVER_ERROR, "code": "server_error"}
    assert "secret" not in str(r.data)


def test_validation_keeps_drf_field_shape():
    r = call(serializers.ValidationError({"phone": ["bad"]}))
    assert r.status_code == 400
    assert r.data == {"phone": ["bad"]}


def test_api_error_with_extra():
    r = call(ApiError("msg", "cart_changed", status.HTTP_409_CONFLICT, {"quote": {"total": 1}}))
    assert r.status_code == 409
    assert r.data == {"detail": "msg", "code": "cart_changed", "quote": {"total": 1}}


def test_pagination_shape_and_page_size():
    factory = APIRequestFactory()
    request = APIView().initialize_request(factory.get("/x/"))
    page = StandardPagination().paginate_queryset(list(range(45)), request)
    assert len(page) == 20
    paginator = StandardPagination()
    paginator.paginate_queryset(list(range(45)), request)
    body = paginator.get_paginated_response(page).data
    assert set(body) == {"count", "next", "previous", "results"}
    assert body["count"] == 45
    assert Response  # keep import used

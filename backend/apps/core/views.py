import hmac

from django.conf import settings
from django.db import connection
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ApiError
from common.throttling import HealthRateThrottle

from .models import ShopSettings
from .serializers import ShopSettingsSerializer

HEALTH_HEADER = "X-Health-Check-Token"


def _provided_password(request) -> str:
    return request.headers.get(HEALTH_HEADER) or request.query_params.get("password") or ""


class HealthView(APIView):
    """Liveness + DB check, protected by HEALTH_CHECK_PASSWORD."""

    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [HealthRateThrottle]

    @extend_schema(
        summary="Health check",
        description=(
            "Send the password in the `X-Health-Check-Token` header (preferred) "
            "or the `password` query parameter."
        ),
        responses={
            200: inline_serializer(
                "Health",
                {"status": serializers.CharField(), "database": serializers.CharField()},
            ),
            403: OpenApiResponse(description="Missing or invalid health password"),
            429: OpenApiResponse(description="Rate limit exceeded"),
            503: OpenApiResponse(description="Database unavailable"),
        },
    )
    def get(self, request):
        expected = settings.HEALTH_CHECK_PASSWORD
        provided = _provided_password(request)
        if not provided:
            raise ApiError(
                "لازم تبعت باسورد الفحص", "health_password_required", status.HTTP_403_FORBIDDEN
            )
        if not expected or not hmac.compare_digest(provided.encode(), expected.encode()):
            raise ApiError("باسورد الفحص غلط", "invalid_health_password", status.HTTP_403_FORBIDDEN)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as exc:  # noqa: BLE001 - never leak internals
            raise ApiError(
                "قاعدة البيانات مش شغالة",
                "db_unavailable",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc
        return Response({"status": "healthy", "database": "ok"})


class SettingsView(RetrieveAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    serializer_class = ShopSettingsSerializer
    pagination_class = None
    filter_backends: list = []

    def get_object(self):
        return ShopSettings.load()

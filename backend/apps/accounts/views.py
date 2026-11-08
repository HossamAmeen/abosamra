from django.contrib.auth import authenticate
from django.db import IntegrityError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenRefreshView

from common.exceptions import ApiError
from common.phone import try_normalize_phone
from common.throttling import AuthRateThrottle

from . import services
from .serializers import (
    AdminLoginSerializer,
    AuthResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .tokens import AppRefreshToken

ERR_429 = OpenApiResponse(description="Rate limit exceeded")


def auth_response(user, http_status=status.HTTP_200_OK):
    return Response(
        {**services.issue_tokens(user), "user": UserSerializer(user).data}, status=http_status
    )


class AuthView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]


class RegisterView(AuthView):
    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: AuthResponseSerializer,
            400: OpenApiResponse(description="Validation error"),
            409: OpenApiResponse(description="phone_exists"),
            429: ERR_429,
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.register_customer(**serializer.validated_data)
        except IntegrityError as exc:  # concurrent duplicate
            raise services.phone_exists_error() from exc
        return auth_response(user, status.HTTP_201_CREATED)


class LoginView(AuthView):
    @extend_schema(
        request=LoginSerializer,
        responses={
            200: AuthResponseSerializer,
            400: OpenApiResponse(description="Invalid phone"),
            404: OpenApiResponse(description="not_found"),
            429: ERR_429,
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.get_customer_by_phone(serializer.validated_data["phone"])
        return auth_response(user)


class AdminLoginView(AuthView):
    @extend_schema(
        request=AdminLoginSerializer,
        responses={
            200: AuthResponseSerializer,
            401: OpenApiResponse(description="Wrong credentials"),
            429: ERR_429,
        },
    )
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = try_normalize_phone(serializer.validated_data["phone"])
        user = (
            authenticate(request, phone=phone, password=serializer.validated_data["password"])
            if phone
            else None
        )
        if user is None or not user.is_staff or not user.is_active:
            raise ApiError(
                "الرقم أو الباسورد غلط", "invalid_credentials", status.HTTP_401_UNAUTHORIZED
            )
        return auth_response(user)


class TokenRefresh(TokenRefreshView):
    serializer_class = RefreshSerializer
    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(responses={200: RefreshSerializer, 401: OpenApiResponse(description="Invalid")})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=LogoutSerializer,
        responses={204: None, 401: OpenApiResponse(description="Invalid refresh token")},
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            AppRefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError as exc:
            raise ApiError(
                "الجلسة خلصت أو مش صالحة، سجل دخول تاني",
                "token_not_valid",
                status.HTTP_401_UNAUTHORIZED,
            ) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = None
    filter_backends: list = []

    def get_object(self):
        return self.request.user

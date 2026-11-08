from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.throttling import OrdersRateThrottle, QuoteRateThrottle

from .models import Order
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    QuoteRequestSerializer,
    QuoteSerializer,
)
from .services import orders as order_service
from .services.pricing import quote


def order_queryset():
    return Order.objects.select_related("customer").prefetch_related("lines", "discounts")


class CartQuoteView(APIView):
    """Price a cart. Works for guests; throttled with the `quote` scope."""

    permission_classes = [AllowAny]
    throttle_classes = [QuoteRateThrottle]

    @extend_schema(
        request=QuoteRequestSerializer,
        responses={
            200: QuoteSerializer,
            400: OpenApiResponse(description="Validation error"),
            429: OpenApiResponse(description="Rate limit exceeded"),
        },
    )
    def post(self, request):
        serializer = QuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response(quote(data["items"], data["bundles"]).to_dict())


class OrderCreateView(CreateAPIView):
    """Place a cash-on-delivery order (server recomputes everything)."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [OrdersRateThrottle]
    serializer_class = OrderCreateSerializer

    @extend_schema(
        request=OrderCreateSerializer,
        responses={
            201: OrderSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Not authenticated"),
            409: OpenApiResponse(description="cart_changed (body carries a fresh `quote`)"),
            429: OpenApiResponse(description="Rate limit exceeded"),
            503: OpenApiResponse(description="Shop is not accepting orders"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = order_service.create_order(request.user, **serializer.validated_data)
        return Response(
            OrderSerializer(order_queryset().get(pk=order.pk)).data, status=status.HTTP_201_CREATED
        )


class MyOrdersView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    filter_backends: list = []

    def get_queryset(self):
        return order_queryset().filter(customer=self.request.user).order_by("-created_at", "-id")


class MyOrderDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    filter_backends: list = []
    pagination_class = None

    def get_queryset(self):
        return order_queryset().filter(customer=self.request.user)

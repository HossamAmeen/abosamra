"""Staff API for orders + dashboard (BSPEC 6, /api/v1/admin/...)."""

from datetime import timedelta

from django.db.models import Count, F, Q, Sum
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.catalog.models import Product
from common.money import money
from common.phone import try_normalize_phone

from .models import Order
from .serializers import AdminOrderSerializer, OrderStatusSerializer
from .services import orders as order_service
from .views import order_queryset


def search_orders(queryset, term: str):
    term = (term or "").strip().lstrip("#")
    if not term:
        return queryset
    condition = Q(customer__name__icontains=term)
    phone = try_normalize_phone(term)
    digits = phone or "".join(ch for ch in term if ch.isdigit())
    if digits:
        condition |= Q(customer__phone__contains=digits)
    if term.isdigit():
        condition |= Q(number=int(term))
    return queryset.filter(condition)


class AdminOrderListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminOrderSerializer
    filter_backends: list = []

    def get_queryset(self):
        qs = order_queryset().order_by("-created_at", "-id")
        status_value = self.request.query_params.get("status")
        if status_value:
            if status_value not in Order.Status.values:
                raise serializers.ValidationError({"status": ["الحالة دي مش موجودة"]})
            qs = qs.filter(status=status_value)
        return search_orders(qs, self.request.query_params.get("q"))

    @extend_schema(
        parameters=[
            OpenApiParameter("status", str, enum=[c for c, _ in Order.Status.choices]),
            OpenApiParameter("q", str, description="order number, customer name or phone"),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminOrderDetailView(RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminOrderSerializer
    http_method_names = ["get", "patch", "head", "options"]
    filter_backends: list = []

    def get_queryset(self):
        return order_queryset()

    @extend_schema(
        request=OrderStatusSerializer,
        responses={
            200: AdminOrderSerializer,
            400: OpenApiResponse(description="Invalid status / transition"),
        },
    )
    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_service.change_status(order, serializer.validated_data["status"], request.user)
        return Response(AdminOrderSerializer(self.get_queryset().get(pk=order.pk)).data)


CountsSerializer = inline_serializer(
    "OrderCounts", {code: serializers.IntegerField() for code, _ in Order.Status.choices}
)


class AdminOrderCountsView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses=CountsSerializer)
    def get(self, request):
        counts = {code: 0 for code, _ in Order.Status.choices}
        for row in Order.objects.values("status").annotate(n=Count("id")):
            counts[row["status"]] = row["n"]
        return Response(counts)


DashboardSerializer = inline_serializer(
    "AdminDashboard",
    {
        "orders_today": serializers.IntegerField(),
        "sales_today": serializers.IntegerField(),
        "pending_count": serializers.IntegerField(),
        "new_customers_week": serializers.IntegerField(),
        "low_stock": inline_serializer(
            "LowStockProduct",
            {
                "id": serializers.IntegerField(),
                "name": serializers.CharField(),
                "stock_qty": serializers.FloatField(),
                "stock_unit": serializers.CharField(),
            },
            many=True,
        ),
    },
)


def _number(value):
    return int(value) if value == int(value) else float(value)


class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses=DashboardSerializer)
    def get(self, request):
        now = timezone.localtime()  # Africa/Cairo
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today = Order.objects.filter(created_at__gte=start)
        sales = today.exclude(status=Order.Status.CANCELLED).aggregate(s=Sum("total"))["s"] or 0
        low_stock = (
            Product.objects.filter(
                is_archived=False,
                stock_qty__isnull=False,
                low_stock_threshold__isnull=False,
                stock_qty__lte=F("low_stock_threshold"),
            )
            .order_by("stock_qty", "id")
            .values("id", "name", "stock_qty", "stock_unit")
        )
        return Response(
            {
                "orders_today": today.count(),
                "sales_today": money(sales),
                "pending_count": Order.objects.filter(status=Order.Status.NEW).count(),
                "new_customers_week": User.objects.filter(
                    is_staff=False, date_joined__gte=now - timedelta(days=7)
                ).count(),
                "low_stock": [{**row, "stock_qty": _number(row["stock_qty"])} for row in low_stock],
            }
        )

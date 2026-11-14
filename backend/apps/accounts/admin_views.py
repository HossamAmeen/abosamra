from decimal import Decimal

from django.db import IntegrityError
from django.db.models import Count, DecimalField, F, Max, Q, Sum, Value
from django.db.models.functions import Coalesce
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.generics import ListAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAdminUser

from apps.orders.admin_views import AdminOrderSerializer
from apps.orders.models import Order
from apps.orders.views import order_queryset
from common.fields import MoneyField, PhoneField
from common.phone import try_normalize_phone

from . import services
from .models import User


class AdminCustomerSerializer(serializers.ModelSerializer):
    orders_count = serializers.IntegerField(read_only=True)
    total_spent = MoneyField(read_only=True)
    last_order_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id", "name", "phone", "email", "default_address", "area",
            "date_joined", "orders_count", "total_spent", "last_order_at",
        ]  # fmt: skip
        read_only_fields = fields


class AdminCustomerListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCustomerSerializer
    filter_backends: list = []

    def get_queryset(self):
        not_cancelled = ~Q(orders__status=Order.Status.CANCELLED)
        qs = (
            User.objects.filter(is_staff=False)
            .annotate(
                orders_count=Count("orders", distinct=True),
                total_spent=Coalesce(
                    Sum("orders__total", filter=not_cancelled),
                    Value(Decimal("0")),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                last_order_at=Max("orders__created_at"),
            )
            .order_by(F("last_order_at").desc(nulls_last=True), "-id")
        )
        term = (self.request.query_params.get("q") or "").strip()
        if term:
            condition = Q(name__icontains=term)
            digits = try_normalize_phone(term) or "".join(c for c in term if c.isdigit())
            if digits:
                condition |= Q(phone__contains=digits)
            qs = qs.filter(condition)
        return qs

    @extend_schema(parameters=[OpenApiParameter("q", str, description="name or phone")])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminCustomerOrdersView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminOrderSerializer
    filter_backends: list = []

    def get_queryset(self):
        customer = get_object_or_404(User, pk=self.kwargs["pk"], is_staff=False)
        return order_queryset().filter(customer=customer).order_by("-created_at", "-id")


NAME_ERRORS = {
    "min_length": "الاسم لازم يكون حرفين على الأقل",
    "max_length": "الاسم طويل أوي (80 حرف بحد أقصى)",
    "required": "اكتب الاسم",
    "blank": "اكتب الاسم",
}
PASSWORD_ERRORS = {
    "min_length": "كلمة السر لازم تكون 8 حروف على الأقل",
    "max_length": "كلمة السر طويلة أوي",
    "required": "اكتب كلمة السر",
    "blank": "اكتب كلمة السر",
}


class AdminStaffSerializer(serializers.ModelSerializer):
    name = serializers.CharField(min_length=2, max_length=80, error_messages=NAME_ERRORS)
    phone = PhoneField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
        trim_whitespace=False,
        error_messages=PASSWORD_ERRORS,
    )

    class Meta:
        model = User
        fields = ["id", "name", "phone", "password", "date_joined"]
        read_only_fields = ["id", "date_joined"]

    def validate_password(self, value):
        if value.isdigit():
            raise serializers.ValidationError("كلمة السر مينفعش تكون أرقام بس")
        return value

    def create(self, validated_data):
        try:
            return services.create_staff(**validated_data)
        except IntegrityError as exc:  # concurrent duplicate
            raise services.staff_phone_exists_error() from exc


class AdminStaffListCreateView(ListCreateAPIView):
    """Staff accounts that can sign in to the dashboard; POST adds a new one."""

    permission_classes = [IsAdminUser]
    serializer_class = AdminStaffSerializer
    filter_backends: list = []

    def get_queryset(self):
        return User.objects.filter(is_staff=True, is_active=True).order_by("date_joined", "id")

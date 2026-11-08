from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from common.fields import MoneyField

from .models import Order, OrderDiscount, OrderLine

MAX_QTY = 50
MAX_ROWS = 100

_QTY = {"min_value": 1, "max_value": MAX_QTY}
_QTY_MESSAGES = {
    "min_value": "الكمية لازم تكون من 1 لـ 50",
    "max_value": "الكمية لازم تكون من 1 لـ 50",
    "invalid": "الكمية لازم تكون رقم صحيح",
    "required": "اكتب الكمية",
}


class QuoteItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    qty = serializers.IntegerField(**_QTY, error_messages=_QTY_MESSAGES)
    note = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")


class QuoteBundleSerializer(serializers.Serializer):
    offer_id = serializers.IntegerField()
    qty = serializers.IntegerField(**_QTY, error_messages=_QTY_MESSAGES)


class QuoteRequestSerializer(serializers.Serializer):
    items = QuoteItemSerializer(many=True, required=False, default=list, max_length=MAX_ROWS)
    bundles = QuoteBundleSerializer(many=True, required=False, default=list, max_length=MAX_ROWS)


class QuoteLineSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(allow_null=True)
    offer_id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField()
    unit_label = serializers.CharField()
    qty = serializers.IntegerField()
    unit_price = serializers.IntegerField()
    line_total = serializers.IntegerField()


class QuoteDiscountSerializer(serializers.Serializer):
    offer_id = serializers.IntegerField()
    label = serializers.CharField()
    amount = serializers.IntegerField()


class QuoteWarningSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(allow_null=True)
    offer_id = serializers.IntegerField(required=False)
    code = serializers.ChoiceField(
        choices=["unavailable", "not_found", "insufficient_stock", "offer_expired"]
    )
    detail = serializers.CharField()


class QuoteSerializer(serializers.Serializer):
    lines = QuoteLineSerializer(many=True)
    subtotal = serializers.IntegerField()
    discounts = QuoteDiscountSerializer(many=True)
    discount_total = serializers.IntegerField()
    delivery_fee = serializers.IntegerField()
    free_delivery_threshold = serializers.IntegerField()
    free_delivery_remaining = serializers.IntegerField()
    total = serializers.IntegerField()
    warnings = QuoteWarningSerializer(many=True)


# ---- Orders (BSPEC 4.4 / 5) -------------------------------------------------


class OrderCreateSerializer(serializers.Serializer):
    items = QuoteItemSerializer(many=True, required=False, default=list, max_length=MAX_ROWS)
    bundles = QuoteBundleSerializer(many=True, required=False, default=list, max_length=MAX_ROWS)
    address = serializers.CharField(
        min_length=10,
        max_length=500,
        error_messages={
            "required": "اكتب عنوان التوصيل",
            "blank": "اكتب عنوان التوصيل",
            "min_length": "اكتب العنوان بالتفصيل (10 حروف على الأقل)",
            "max_length": "العنوان طويل أوي",
        },
    )
    area = serializers.CharField(max_length=80, required=False, allow_blank=True, default="")
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class OrderLineSerializer(serializers.ModelSerializer):
    unit_price = MoneyField(read_only=True)
    line_total = MoneyField(read_only=True)

    class Meta:
        model = OrderLine
        fields = ["name", "unit_label", "qty", "unit_price", "line_total", "note"]


class OrderDiscountSerializer(serializers.ModelSerializer):
    offer_id = serializers.IntegerField(read_only=True, allow_null=True)
    amount = MoneyField(read_only=True)

    class Meta:
        model = OrderDiscount
        fields = ["offer_id", "label", "amount"]


class OrderCustomerSerializer(serializers.Serializer):
    name = serializers.CharField()
    phone = serializers.CharField()


class OrderSerializer(serializers.ModelSerializer):
    customer = OrderCustomerSerializer(read_only=True)
    lines = OrderLineSerializer(many=True, read_only=True)
    discounts = OrderDiscountSerializer(many=True, read_only=True)
    subtotal = MoneyField(read_only=True)
    discount_total = MoneyField(read_only=True)
    delivery_fee = MoneyField(read_only=True)
    total = MoneyField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "number",
            "status",
            "created_at",
            "customer",
            "address",
            "area",
            "notes",
            "lines",
            "subtotal",
            "discounts",
            "discount_total",
            "delivery_fee",
            "total",
            "payment_method",
        ]
        read_only_fields = fields


class AdminOrderSerializer(OrderSerializer):
    items_summary = serializers.SerializerMethodField()

    class Meta(OrderSerializer.Meta):
        fields = [*OrderSerializer.Meta.fields, "items_summary"]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField())
    def get_items_summary(self, obj):
        """'كمون مطحون ×2، فلفل أسود، عسل نحل' (first 3 lines, then '…')."""
        lines = list(obj.lines.all())
        parts = [f"{ln.name} ×{ln.qty}" if ln.qty > 1 else ln.name for ln in lines[:3]]
        text = "، ".join(parts)
        return f"{text}…" if len(lines) > 3 else text


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=Order.Status.choices, error_messages={"invalid_choice": "الحالة دي مش صحيحة"}
    )

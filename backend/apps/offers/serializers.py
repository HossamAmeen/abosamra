from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers

from common.fields import MoneyField
from common.money import money

from .models import Offer

Target = inline_serializer(
    "OfferTarget",
    {
        "kind": serializers.CharField(),
        "slug": serializers.CharField(allow_null=True),
        "ids": serializers.ListField(child=serializers.IntegerField()),
    },
)
BundleItemOut = inline_serializer(
    "OfferBundleItem",
    {
        "variant_id": serializers.IntegerField(),
        "name": serializers.CharField(),
        "qty": serializers.IntegerField(),
    },
    many=True,
)


class OfferSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    bundle_items = serializers.SerializerMethodField()
    bundle_price = MoneyField(read_only=True, allow_null=True)
    old_price = serializers.SerializerMethodField()
    min_order = MoneyField(read_only=True, allow_null=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "type",
            "name",
            "description",
            "value",
            "target",
            "bundle_items",
            "bundle_price",
            "old_price",
            "min_order",
            "starts_at",
            "ends_at",
            "is_featured",
        ]

    def get_value(self, obj) -> float | int | None:
        if obj.value is None:
            return None
        return int(obj.value) if obj.value == int(obj.value) else float(obj.value)

    @extend_schema_field(Target)
    def get_target(self, obj):
        slug = None
        ids: list[int] = []
        if obj.target_kind == Offer.Target.CATEGORY and obj.target_category_id:
            slug = obj.target_category.slug
        elif obj.target_kind == Offer.Target.PRODUCTS:
            ids = sorted(p.id for p in obj.target_products.all())
        return {"kind": obj.target_kind, "slug": slug, "ids": ids}

    @extend_schema_field(BundleItemOut)
    def get_bundle_items(self, obj):
        return [
            {
                "variant_id": item.variant_id,
                "name": f"{item.variant.product.name} {item.variant.label}",
                "qty": item.qty,
            }
            for item in obj.bundle_items.all()
        ]

    def get_old_price(self, obj) -> int | None:
        if obj.type != Offer.Type.BUNDLE:
            return None
        return money(sum(item.variant.price * item.qty for item in obj.bundle_items.all()))

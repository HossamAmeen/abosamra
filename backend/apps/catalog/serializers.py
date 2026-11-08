from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers

from apps.offers.selectors import best_offer_for, live_percentage_offers
from common.fields import MoneyField

from .models import Category, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "slug", "name", "color", "icon", "order"]


class CategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["slug", "name", "color", "icon"]


class VariantSerializer(serializers.ModelSerializer):
    price = MoneyField(read_only=True)
    old_price = MoneyField(source="compare_at_price", read_only=True, allow_null=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "label", "price", "old_price", "is_default"]


ActiveOffer = inline_serializer(
    "ActiveOffer",
    {
        "id": serializers.IntegerField(),
        "name": serializers.CharField(),
        "type": serializers.CharField(),
        "value": serializers.FloatField(),
    },
    allow_null=True,
)


def _number(value):
    return int(value) if value == int(value) else float(value)


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True, allow_null=True)
    category = CategoryBriefSerializer(read_only=True)
    variants = VariantSerializer(many=True, read_only=True)
    active_offer = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "image",
            "is_available",
            "is_featured",
            "category",
            "variants",
            "active_offer",
        ]

    def _live_offers(self):
        # Fetched once per serializer tree (one query for the whole page).
        root = self.root
        if not hasattr(root, "_live_offers_cache"):
            root._live_offers_cache = live_percentage_offers()
        return root._live_offers_cache

    @extend_schema_field(ActiveOffer)
    def get_active_offer(self, obj):
        offer = best_offer_for(obj.id, obj.category_id, self._live_offers())
        if offer is None:
            return None
        return {
            "id": offer.id,
            "name": offer.name,
            "type": "percentage",
            "value": _number(offer.value),
        }

"""Staff serializers for products with nested variants (BSPEC 6, /admin/products/)."""

import json

from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.offers.models import BundleItem
from common.fields import MoneyField

from .models import Category, Product, ProductVariant
from .serializers import CategoryBriefSerializer


class AdminVariantSerializer(serializers.ModelSerializer):
    """Read: price/old_price rounded to whole pounds. Write: any positive decimal."""

    id = serializers.IntegerField(required=False)
    old_price = serializers.DecimalField(
        source="compare_at_price",
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=0,
    )
    is_default = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = ProductVariant
        fields = ["id", "label", "price", "old_price", "stock_factor", "is_default", "order"]
        extra_kwargs = {
            "label": {
                "error_messages": {"required": "اكتب الوزن", "blank": "اكتب الوزن"},
            },
            "price": {
                "min_value": 0,
                "error_messages": {"required": "اكتب السعر", "invalid": "اكتب سعر صحيح"},
            },
            "stock_factor": {"required": False, "min_value": 0},
            "order": {"required": False},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["price"] = MoneyField().to_representation(instance.price)
        if instance.compare_at_price is not None:
            data["old_price"] = MoneyField().to_representation(instance.compare_at_price)
        data["stock_factor"] = float(instance.stock_factor)
        return data


@extend_schema_field(AdminVariantSerializer(many=True))
class VariantsField(serializers.Field):
    """`variants` as a JSON list (JSON body) or a JSON string (multipart form field)."""

    default_error_messages = {
        "invalid_json": "الأوزان لازم تتبعت بصيغة صحيحة",
        "empty": "ضيف وزن واحد على الأقل",
    }

    def get_value(self, dictionary):
        # Bypass DRF's HTML list parsing: read the raw value from QueryDict or dict.
        return dictionary.get(self.field_name, serializers.empty)

    def to_internal_value(self, data):
        if isinstance(data, str | bytes):
            try:
                data = json.loads(data)
            except ValueError:
                self.fail("invalid_json")
        if not isinstance(data, list):
            self.fail("invalid_json")
        if not data:
            self.fail("empty")
        child = AdminVariantSerializer(many=True)
        return child.run_validation(data)

    def to_representation(self, value):
        ordered = sorted(value.all(), key=lambda v: (not v.is_default, v.order, v.id))
        return AdminVariantSerializer(ordered, many=True).data


class CategoryRefField(serializers.PrimaryKeyRelatedField):
    """Write: category id or slug. Read: {id, slug, name, color, icon}."""

    def __init__(self, **kwargs):
        kwargs.setdefault("queryset", Category.objects.all())
        kwargs.setdefault("error_messages", {})
        kwargs["error_messages"].setdefault("does_not_exist", "القسم ده مش موجود")
        kwargs["error_messages"].setdefault("incorrect_type", "القسم ده مش موجود")
        kwargs["error_messages"].setdefault("required", "اختار القسم")
        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        if isinstance(data, str) and not data.isdigit():
            try:
                return self.get_queryset().get(slug=data)
            except Category.DoesNotExist:
                self.fail("does_not_exist", pk_value=data)
        return super().to_internal_value(data)

    def to_representation(self, value):
        return {"id": value.pk, **CategoryBriefSerializer(value).data}


class AdminProductSerializer(serializers.ModelSerializer):
    category = CategoryRefField()
    image = serializers.ImageField(required=False, allow_null=True)
    variants = VariantsField(required=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "image",
            "category",
            "is_available",
            "is_featured",
            "stock_qty",
            "low_stock_threshold",
            "stock_unit",
            "variants",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]
        extra_kwargs = {
            "name": {
                "min_length": 2,
                "error_messages": {
                    "required": "اكتب اسم المنتج",
                    "blank": "اكتب اسم المنتج",
                    "min_length": "اسم المنتج قصير أوي",
                },
            },
            "stock_qty": {"min_value": 0},
            "low_stock_threshold": {"min_value": 0},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key in ("stock_qty", "low_stock_threshold"):
            if data[key] is not None:
                data[key] = float(data[key])
        return data

    def validate_variants(self, variants):
        defaults = [v for v in variants if v.get("is_default")]
        if len(defaults) > 1:
            raise serializers.ValidationError("لازم وزن واحد بس يكون الافتراضي")
        if not defaults:
            variants[0]["is_default"] = True  # first variant is the default
        return variants

    # -- writes ---------------------------------------------------------------
    @transaction.atomic
    def create(self, validated_data):
        variants = validated_data.pop("variants")
        product = Product.objects.create(**validated_data)
        self._sync_variants(product, variants)
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        variants = validated_data.pop("variants", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if variants is not None:
            self._sync_variants(instance, variants)
        return instance

    def _sync_variants(self, product, variants):
        """Replace-by-id: ids update, no id creates, existing ids not sent are deleted."""
        existing = {v.id: v for v in product.variants.all()}
        sent_ids = {v["id"] for v in variants if v.get("id")}
        unknown = sent_ids - existing.keys()
        if unknown:
            raise serializers.ValidationError({"variants": ["وزن مش تابع للمنتج ده"]})
        removed = set(existing) - sent_ids
        if removed and BundleItem.objects.filter(variant_id__in=removed).exists():
            raise serializers.ValidationError(
                {"variants": ["الوزن ده داخل في باكدج، شيله من الباكدج الأول"]}
            )
        ProductVariant.objects.filter(id__in=removed).delete()
        # Free the "one default" slot before writing the new default.
        product.variants.filter(is_default=True).update(is_default=False)
        for index, item in enumerate(variants):
            item = {**item}
            variant_id = item.pop("id", None)
            item.setdefault("order", index)
            if variant_id:
                for attr, value in item.items():
                    setattr(existing[variant_id], attr, value)
                existing[variant_id].save()
            else:
                ProductVariant.objects.create(product=product, **item)

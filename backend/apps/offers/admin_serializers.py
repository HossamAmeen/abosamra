"""Staff serializer for offers with nested bundle items (BSPEC 6, /admin/offers/).

Round-trips the public Offer shape: `target: {kind, slug, ids}` and
`bundle_items: [{variant_id, qty}]`.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.catalog.models import Category, Product, ProductVariant
from common.money import money

from .models import BundleItem, Offer
from .serializers import OfferSerializer


class TargetInSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=Offer.Target.choices)
    slug = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ids = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=True)


class BundleItemInSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    qty = serializers.IntegerField(
        min_value=1, max_value=50, error_messages={"min_value": "الكمية لازم تكون 1 على الأقل"}
    )


def _django_to_drf(exc: DjangoValidationError):
    if hasattr(exc, "message_dict"):
        return serializers.ValidationError(exc.message_dict)
    return serializers.ValidationError(exc.messages)


class AdminOfferSerializer(OfferSerializer):
    # Writable overrides of the read-only public fields.
    value = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )
    bundle_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    min_order = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    target = TargetInSerializer(required=False)
    bundle_items = BundleItemInSerializer(many=True, required=False)

    class Meta(OfferSerializer.Meta):
        fields = [*OfferSerializer.Meta.fields, "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "name": {"error_messages": {"required": "اكتب اسم العرض", "blank": "اكتب اسم العرض"}},
            "starts_at": {"required": False},
        }

    # -- representation -------------------------------------------------------
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["value"] = self.get_value(instance)
        data["target"] = self.get_target(instance)
        data["bundle_items"] = self.get_bundle_items(instance)
        data["bundle_price"] = (
            None if instance.bundle_price is None else money(instance.bundle_price)
        )
        data["min_order"] = None if instance.min_order is None else money(instance.min_order)
        return data

    # -- validation -----------------------------------------------------------
    def validate(self, attrs):
        target = attrs.pop("target", None)
        items = attrs.get("bundle_items")
        if target is not None:
            attrs["target_kind"] = target["kind"]
            attrs["_target_ids"] = target.get("ids") or []
            slug = target.get("slug")
            category = None
            if target["kind"] == Offer.Target.CATEGORY:
                category = Category.objects.filter(slug=slug or "").first()
                if category is None:
                    raise serializers.ValidationError({"target": ["اختار القسم"]})
            attrs["target_category"] = category
            if target["kind"] == Offer.Target.PRODUCTS:
                ids = set(attrs["_target_ids"])
                found = set(Product.objects.filter(id__in=ids).values_list("id", flat=True))
                if not ids or ids != found:
                    raise serializers.ValidationError({"target": ["اختار منتج واحد على الأقل"]})
        if items is not None:
            ids = {i["variant_id"] for i in items}
            if len(items) != len(ids):
                raise serializers.ValidationError({"bundle_items": ["الوزن اتكرر في الباكدج"]})
            found = set(ProductVariant.objects.filter(id__in=ids).values_list("id", flat=True))
            if ids != found:
                raise serializers.ValidationError({"bundle_items": ["فيه وزن مش موجود"]})

        # Model-level checks on the merged state.
        candidate = self._candidate(attrs)
        try:
            candidate.clean()
        except DjangoValidationError as exc:
            raise _django_to_drf(exc) from exc
        return attrs

    def _candidate(self, attrs) -> Offer:
        fields = [
            "type", "value", "target_kind", "target_category", "bundle_price",
            "min_order", "starts_at", "ends_at",
        ]  # fmt: skip
        source = self.instance or Offer()
        candidate = Offer(**{f: getattr(source, f) for f in fields})
        for f in fields:
            if f in attrs:
                setattr(candidate, f, attrs[f])
        return candidate

    # -- writes ---------------------------------------------------------------
    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("bundle_items", [])
        product_ids = validated_data.pop("_target_ids", [])
        offer = Offer.objects.create(**validated_data)
        self._write_relations(offer, items, product_ids, items_given=True, targets_given=True)
        return offer

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("bundle_items", None)
        product_ids = validated_data.pop("_target_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self._write_relations(
            instance,
            items or [],
            product_ids or [],
            items_given=items is not None,
            targets_given=product_ids is not None,
        )
        return instance

    def _write_relations(self, offer, items, product_ids, *, items_given, targets_given):
        if items_given:
            offer.bundle_items.all().delete()
            BundleItem.objects.bulk_create(
                BundleItem(offer=offer, variant_id=i["variant_id"], qty=i["qty"]) for i in items
            )
        if targets_given:
            offer.target_products.set(product_ids)
        if offer.target_kind != Offer.Target.PRODUCTS:
            offer.target_products.clear()
        try:
            offer.validate_relations()
        except DjangoValidationError as exc:
            raise _django_to_drf(exc) from exc

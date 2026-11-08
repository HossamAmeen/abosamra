from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Category, Product, ProductVariant

PERCENT_MIN, PERCENT_MAX = 1, 90


class OfferQuerySet(models.QuerySet):
    def live(self, now=None):
        now = now or timezone.now()
        return self.filter(is_active=True, starts_at__lte=now).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=now)
        )


class Offer(models.Model):
    class Type(models.TextChoices):
        PERCENTAGE = "percentage", "نسبة خصم"
        BUNDLE = "bundle", "باكدج"
        FREE_DELIVERY = "free_delivery", "توصيل مجاني"

    class Target(models.TextChoices):
        CATEGORY = "category", "قسم"
        PRODUCTS = "products", "منتجات"
        ALL = "all", "الكل"

    type = models.CharField("النوع", max_length=20, choices=Type.choices)
    name = models.CharField("الاسم", max_length=120)
    description = models.TextField("الوصف", blank=True)
    value = models.DecimalField("النسبة %", max_digits=5, decimal_places=2, null=True, blank=True)
    target_kind = models.CharField(
        "الهدف", max_length=20, choices=Target.choices, default=Target.ALL
    )
    target_category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.CASCADE, related_name="offers"
    )
    target_products = models.ManyToManyField(Product, blank=True, related_name="offers")
    bundle_price = models.DecimalField(
        "سعر الباكدج", max_digits=10, decimal_places=2, null=True, blank=True
    )
    min_order = models.DecimalField(
        "أقل طلب", max_digits=10, decimal_places=2, null=True, blank=True
    )
    starts_at = models.DateTimeField("يبدأ", default=timezone.now)
    ends_at = models.DateTimeField("ينتهي", null=True, blank=True)
    is_active = models.BooleanField("شغال", default=True)
    is_featured = models.BooleanField("عرض الأسبوع", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OfferQuerySet.as_manager()

    class Meta:
        ordering = ["-is_featured", "-created_at", "-id"]
        verbose_name = "عرض"
        verbose_name_plural = "العروض"

    def __str__(self):
        return self.name

    def clean(self):
        errors = {}
        if self.type == self.Type.PERCENTAGE:
            if self.value is None or not (PERCENT_MIN <= self.value <= PERCENT_MAX):
                errors["value"] = "النسبة لازم تكون من 1 لـ 90"
            if self.target_kind == self.Target.CATEGORY and not self.target_category_id:
                errors["target_category"] = "اختار القسم"
            # `products` targets live in an M2M, validated once the offer has been saved.
        elif self.type == self.Type.BUNDLE:
            if self.bundle_price is None or self.bundle_price <= 0:
                errors["bundle_price"] = "اكتب سعر الباكدج"
        elif self.type == self.Type.FREE_DELIVERY:
            if self.min_order is None or self.min_order < 0:
                errors["min_order"] = "اكتب أقل قيمة للطلب"
        if self.ends_at and self.starts_at and self.ends_at <= self.starts_at:
            errors["ends_at"] = "تاريخ النهاية لازم يبقى بعد البداية"
        if errors:
            raise ValidationError(errors)

    def validate_relations(self):
        """Checks that need saved related rows (call after the M2M / items are written)."""
        if self.type == self.Type.BUNDLE and self.bundle_items.count() < 2:
            raise ValidationError({"bundle_items": "الباكدج لازم فيه منتجين على الأقل"})
        if (
            self.type == self.Type.PERCENTAGE
            and self.target_kind == self.Target.PRODUCTS
            and not self.target_products.exists()
        ):
            raise ValidationError({"target_products": "اختار منتج واحد على الأقل"})


class BundleItem(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="bundle_items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="+")
    qty = models.PositiveIntegerField("الكمية", default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(qty__gte=1), name="bundle_item_qty_gte_1"),
        ]
        verbose_name = "عنصر باكدج"
        verbose_name_plural = "عناصر الباكدج"

    def __str__(self):
        return f"{self.variant_id}×{self.qty}"

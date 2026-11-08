import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from common.images import process_image
from common.models import TimeStampedModel


class Category(models.Model):
    slug = models.SlugField("المعرّف", unique=True)
    name = models.CharField("الاسم", max_length=80)
    color = models.CharField("اللون", max_length=9, default="#F6D9B8")
    icon = models.CharField("الأيقونة", max_length=40, blank=True)
    order = models.PositiveIntegerField("الترتيب", default=0)
    is_active = models.BooleanField("ظاهر", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "قسم"
        verbose_name_plural = "الأقسام"

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products", verbose_name="القسم"
    )
    name = models.CharField("الاسم", max_length=120)
    slug = models.SlugField("المعرّف", max_length=160, unique=True, allow_unicode=True, blank=True)
    description = models.TextField("الوصف", blank=True)
    image = models.ImageField("الصورة", upload_to="products/", blank=True, null=True)
    is_available = models.BooleanField("متاح", default=True)
    is_featured = models.BooleanField("مميز", default=False)
    is_archived = models.BooleanField("مؤرشف", default=False)
    stock_qty = models.DecimalField(
        "الكمية في المخزن", max_digits=10, decimal_places=3, null=True, blank=True
    )
    low_stock_threshold = models.DecimalField(
        "حد التنبيه", max_digits=10, decimal_places=3, null=True, blank=True
    )
    stock_unit = models.CharField("وحدة المخزن", max_length=30, blank=True)

    class Meta:
        indexes = [models.Index(fields=["category", "is_available"])]
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"

    def __str__(self):
        return self.name

    def _make_slug(self) -> str:
        base = slugify(self.name, allow_unicode=True)[:150] or "product"
        slug = base
        while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{uuid.uuid4().hex[:6]}"
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._make_slug()
        if self.image and not getattr(self.image, "_committed", True):
            self.image = process_image(self.image.file)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants", verbose_name="المنتج"
    )
    label = models.CharField("الوزن/الوحدة", max_length=40)
    price = models.DecimalField("السعر", max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        "السعر القديم", max_digits=10, decimal_places=2, null=True, blank=True
    )
    stock_factor = models.DecimalField(
        "معامل المخزن", max_digits=8, decimal_places=3, default=Decimal("1")
    )
    is_default = models.BooleanField("الافتراضي", default=False)
    order = models.PositiveIntegerField("الترتيب", default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_default=True),
                name="unique_default_variant_per_product",
            )
        ]
        verbose_name = "وزن"
        verbose_name_plural = "الأوزان"

    def __str__(self):
        return f"{self.product_id}:{self.label}"

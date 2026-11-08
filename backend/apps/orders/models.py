from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "جديد"
        PREPARING = "preparing", "بيتجهز"
        OUT_FOR_DELIVERY = "out_for_delivery", "في الطريق"
        DELIVERED = "delivered", "اتسلم"
        CANCELLED = "cancelled", "اتلغى"

    class Payment(models.TextChoices):
        COD = "cod", "الدفع عند الاستلام"

    number = models.PositiveIntegerField("رقم الطلب", unique=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="العميل",
    )
    status = models.CharField("الحالة", max_length=20, choices=Status.choices, default=Status.NEW)
    address = models.TextField("العنوان")
    area = models.CharField("المنطقة", max_length=80, blank=True)
    notes = models.TextField("ملاحظات", blank=True)
    subtotal = models.DecimalField("المجموع", max_digits=10, decimal_places=2)
    discount_total = models.DecimalField("الخصم", max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField("التوصيل", max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField("الإجمالي", max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        "طريقة الدفع", max_length=10, choices=Payment.choices, default=Payment.COD
    )
    # {product_id: "amount"} of tracked stock taken by this order; used to restore on cancel.
    stock_deductions = models.JSONField(default=dict, blank=True, editable=False)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["customer", "created_at"]),
        ]
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"

    def __str__(self):
        return f"#{self.number}"


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey(
        "catalog.ProductVariant", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    bundle_offer = models.ForeignKey(
        "offers.Offer", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    name = models.CharField("الاسم", max_length=160)
    unit_label = models.CharField("الوحدة", max_length=40, blank=True)
    unit_price = models.DecimalField("سعر الوحدة", max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField("الكمية")
    line_total = models.DecimalField("الإجمالي", max_digits=10, decimal_places=2)
    note = models.CharField("ملاحظة", max_length=200, blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "بند طلب"
        verbose_name_plural = "بنود الطلب"

    def __str__(self):
        return f"{self.name} ×{self.qty}"


class OrderDiscount(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="discounts")
    offer = models.ForeignKey(
        "offers.Offer", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    label = models.CharField("العرض", max_length=120)
    amount = models.DecimalField("القيمة", max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]
        verbose_name = "خصم طلب"
        verbose_name_plural = "خصومات الطلب"

    def __str__(self):
        return self.label


class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField("من", max_length=20, blank=True, null=True)
    to_status = models.CharField("إلى", max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "سجل حالة"
        verbose_name_plural = "سجل الحالات"

    def __str__(self):
        return f"{self.from_status} -> {self.to_status}"

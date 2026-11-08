from decimal import Decimal

from django.db import models


class ShopSettings(models.Model):
    """Singleton (pk=1). Use `ShopSettings.load()`."""

    shop_name = models.CharField("اسم المحل", max_length=80, default="أبو سمرة")
    phone = models.CharField("التليفون", max_length=20, blank=True)
    whatsapp = models.CharField("واتساب", max_length=20, blank=True)
    delivery_fee = models.DecimalField(
        "مصاريف التوصيل", max_digits=10, decimal_places=2, default=Decimal("30")
    )
    free_delivery_threshold = models.DecimalField(
        "حد التوصيل المجاني", max_digits=10, decimal_places=2, default=Decimal("500")
    )
    is_accepting_orders = models.BooleanField("بياخد طلبات", default=True)

    class Meta:
        verbose_name = "إعدادات المحل"
        verbose_name_plural = "إعدادات المحل"

    def __str__(self):
        return self.shop_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return 0, {}  # singleton: never deleted

    @classmethod
    def load(cls) -> "ShopSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

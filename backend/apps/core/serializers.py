from rest_framework import serializers

from common.fields import MoneyField

from .models import ShopSettings


class ShopSettingsSerializer(serializers.ModelSerializer):
    delivery_fee = MoneyField(read_only=True)
    free_delivery_threshold = MoneyField(read_only=True)
    currency = serializers.SerializerMethodField()

    class Meta:
        model = ShopSettings
        fields = [
            "shop_name",
            "phone",
            "whatsapp",
            "delivery_fee",
            "free_delivery_threshold",
            "currency",
            "is_accepting_orders",
        ]

    def get_currency(self, obj) -> str:
        return "EGP"

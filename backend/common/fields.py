from rest_framework import serializers

from common.messages import PHONE_INVALID
from common.phone import normalize_phone


class PhoneField(serializers.CharField):
    """Accepts any supported phone format, yields the normalized value."""

    default_error_messages = {
        "required": "اكتب رقم الموبايل",
        "blank": "اكتب رقم الموبايل",
        "null": "اكتب رقم الموبايل",
        "invalid": PHONE_INVALID,
    }

    def to_internal_value(self, data):
        return normalize_phone(super().to_internal_value(data))


class MoneyField(serializers.DecimalField):
    """Read-only style money output: JSON number rounded to whole pounds."""

    def __init__(self, **kwargs):
        kwargs.setdefault("max_digits", 10)
        kwargs.setdefault("decimal_places", 2)
        super().__init__(**kwargs)

    def to_representation(self, value):
        from common.money import money

        return money(value)

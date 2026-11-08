import pytest
from django.core.exceptions import ValidationError

from common.messages import PHONE_INVALID
from common.phone import normalize_phone, try_normalize_phone


@pytest.mark.parametrize(
    "raw",
    [
        "٠١٠١٢٣٤٥٦٧٨",
        "۰۱۰۱۲۳۴۵۶۷۸",
        "+201012345678",
        "00201012345678",
        "201012345678",
        "01012345678",
        " 0101-234 (5678) ",
    ],
)
def test_normalizes_to_canonical(raw):
    assert normalize_phone(raw) == "01012345678"


@pytest.mark.parametrize("raw", ["0101234567", "02123456789", "01312345678", "", None, "abc"])
def test_rejects_invalid(raw):
    with pytest.raises(ValidationError) as exc:
        normalize_phone(raw)
    assert exc.value.messages == [PHONE_INVALID]
    assert try_normalize_phone(raw) is None

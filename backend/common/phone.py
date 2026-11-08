"""Phone normalization: the single utility used everywhere (4.1)."""

import re

from django.core.exceptions import ValidationError

from common.messages import PHONE_INVALID

_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_NOISE = re.compile(r"[\s\-()]")
_EGYPT_MOBILE = re.compile(r"^01[0125][0-9]{8}$")


def normalize_phone(value) -> str:
    """Return the canonical 11-digit Egyptian mobile or raise ValidationError."""
    s = str(value or "").translate(_DIGITS)
    s = _NOISE.sub("", s)
    if s.startswith("+20"):
        s = "0" + s[3:]
    elif s.startswith("0020"):
        s = "0" + s[4:]
    elif s.startswith("20") and len(s) == 12:
        s = "0" + s[2:]
    if not _EGYPT_MOBILE.match(s):
        raise ValidationError(PHONE_INVALID, code="invalid_phone")
    return s


def try_normalize_phone(value) -> str | None:
    try:
        return normalize_phone(value)
    except ValidationError:
        return None

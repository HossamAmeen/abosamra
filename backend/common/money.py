from decimal import ROUND_HALF_UP, Decimal


def round_half_up(value) -> Decimal:
    """Whole pounds, round half up (32.25 -> 32, 32.5 -> 33)."""
    return Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def money(value) -> int:
    """JSON-ready whole-pound amount."""
    return int(round_half_up(value))

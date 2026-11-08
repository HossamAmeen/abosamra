"""Pricing engine (BSPEC 4.3): one function shared by /cart/quote/ and order creation."""

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from django.utils import timezone

from apps.catalog.models import Product, ProductVariant
from apps.core.models import ShopSettings
from apps.offers.models import Offer
from apps.offers.selectors import best_offer_for, live_percentage_offers
from common.money import money, round_half_up

UNAVAILABLE = "unavailable"
NOT_FOUND = "not_found"
INSUFFICIENT_STOCK = "insufficient_stock"
OFFER_EXPIRED = "offer_expired"

DETAILS = {
    UNAVAILABLE: "المنتج ده خلصان دلوقتي",
    NOT_FOUND: "المنتج ده مش موجود",
    INSUFFICIENT_STOCK: "الكمية المطلوبة مش متوفرة",
    OFFER_EXPIRED: "العرض ده خلص",
}


@dataclass
class QuoteLine:
    name: str
    unit_label: str
    qty: int
    unit_price: Decimal
    variant_id: int | None = None
    offer_id: int | None = None
    note: str = ""
    # Internal: used for discounts / stock handling by order creation.
    variant: ProductVariant | None = field(default=None, repr=False)
    offer: Offer | None = field(default=None, repr=False)

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.qty


@dataclass
class Quote:
    lines: list[QuoteLine]
    subtotal: Decimal
    discounts: list[dict]  # {offer_id, label, amount: Decimal}
    discount_total: Decimal
    delivery_fee: Decimal
    free_delivery_threshold: Decimal
    free_delivery_remaining: Decimal
    total: Decimal
    warnings: list[dict]

    def to_dict(self) -> dict:
        """JSON-ready: money as whole-pound numbers."""
        return {
            "lines": [
                {
                    "variant_id": ln.variant_id,
                    "offer_id": ln.offer_id,
                    "name": ln.name,
                    "unit_label": ln.unit_label,
                    "qty": ln.qty,
                    "unit_price": money(ln.unit_price),
                    "line_total": money(ln.line_total),
                }
                for ln in self.lines
            ],
            "subtotal": money(self.subtotal),
            "discounts": [{**d, "amount": money(d["amount"])} for d in self.discounts],
            "discount_total": money(self.discount_total),
            "delivery_fee": money(self.delivery_fee),
            "free_delivery_threshold": money(self.free_delivery_threshold),
            "free_delivery_remaining": money(self.free_delivery_remaining),
            "total": money(self.total),
            "warnings": self.warnings,
        }


def _warn(code, *, variant_id=None, offer_id=None) -> dict:
    warning = {"variant_id": variant_id, "code": code, "detail": DETAILS[code]}
    if offer_id is not None:
        warning["offer_id"] = offer_id
    return warning


def _merge_items(items) -> dict[int, dict]:
    merged: dict[int, dict] = {}
    for item in items or []:
        entry = merged.setdefault(item["variant_id"], {"qty": 0, "note": ""})
        entry["qty"] += int(item["qty"])
        entry["note"] = entry["note"] or item.get("note", "")
    return merged


def quote(items, bundles, now=None, *, for_update: bool = False) -> Quote:
    """items: [{variant_id, qty, note?}], bundles: [{offer_id, qty}].

    `for_update=True` locks the involved products (call inside `transaction.atomic()`).
    """
    now = now or timezone.now()
    shop = ShopSettings.load()
    warnings: list[dict] = []
    lines: list[QuoteLine] = []

    merged_items = _merge_items(items)
    merged_bundles: dict[int, int] = defaultdict(int)
    for bundle in bundles or []:
        merged_bundles[bundle["offer_id"]] += int(bundle["qty"])

    live_bundles = {
        o.id: o
        for o in Offer.objects.live(now)
        .filter(id__in=merged_bundles, type=Offer.Type.BUNDLE)
        .prefetch_related("bundle_items")
    }
    bundle_variant_ids = {
        bi.variant_id for offer in live_bundles.values() for bi in offer.bundle_items.all()
    }

    variants = {
        v.id: v
        for v in ProductVariant.objects.filter(
            id__in={*merged_items, *bundle_variant_ids}
        ).select_related("product__category")
    }
    if for_update:
        # Lock the product rows (tracked stock) for the rest of the transaction.
        list(
            Product.objects.select_for_update()
            .filter(id__in={v.product_id for v in variants.values()})
            .values_list("id", flat=True)
        )
        variants = {
            v.id: v
            for v in ProductVariant.objects.filter(id__in=variants).select_related(
                "product__category"
            )
        }

    consumed: dict[int, Decimal] = defaultdict(Decimal)  # product_id -> stock units used

    def check(variant, qty, offer_id=None):
        """Return a warning code, or None when `qty` of `variant` can be sold."""
        if variant is None:
            return NOT_FOUND
        product = variant.product
        if product.is_archived or not product.is_available or not product.category.is_active:
            return UNAVAILABLE
        if product.stock_qty is not None:
            needed = consumed[product.id] + variant.stock_factor * qty
            if needed > product.stock_qty:
                return INSUFFICIENT_STOCK
        return None

    for variant_id, entry in merged_items.items():
        variant = variants.get(variant_id)
        code = check(variant, entry["qty"])
        if code:
            warnings.append(_warn(code, variant_id=variant_id))
            continue
        consumed[variant.product_id] += variant.stock_factor * entry["qty"]
        lines.append(
            QuoteLine(
                name=variant.product.name,
                unit_label=variant.label,
                qty=entry["qty"],
                unit_price=variant.price,
                variant_id=variant.id,
                note=entry["note"],
                variant=variant,
            )
        )

    for offer_id, qty in merged_bundles.items():
        offer = live_bundles.get(offer_id)
        if offer is None or offer.bundle_price is None:
            warnings.append(_warn(OFFER_EXPIRED, offer_id=offer_id))
            continue
        problem = None
        planned: dict[int, Decimal] = defaultdict(Decimal)
        for bi in offer.bundle_items.all():
            variant = variants.get(bi.variant_id)
            if variant is not None:
                # stock check includes what this bundle itself already needs
                saved = consumed[variant.product_id]
                consumed[variant.product_id] = saved + planned[variant.product_id]
            code = check(variant, bi.qty * qty)
            if variant is not None:
                consumed[variant.product_id] = saved
            if code:
                problem = (code, bi.variant_id)
                break
            planned[variant.product_id] += variant.stock_factor * bi.qty * qty
        if problem:
            warnings.append(_warn(problem[0], variant_id=problem[1], offer_id=offer_id))
            continue
        for product_id, used in planned.items():
            consumed[product_id] += used
        lines.append(
            QuoteLine(
                name=offer.name,
                unit_label="",
                qty=qty,
                unit_price=offer.bundle_price,
                offer_id=offer.id,
                offer=offer,
            )
        )

    subtotal = sum((ln.line_total for ln in lines), Decimal("0"))

    # Percentage offers: only the single best one per regular line (no stacking, no bundles).
    percentage_offers = live_percentage_offers(now)
    per_offer: dict[int, Decimal] = defaultdict(Decimal)
    names: dict[int, str] = {}
    for ln in lines:
        if ln.variant is None:
            continue
        best = best_offer_for(
            ln.variant.product_id, ln.variant.product.category_id, percentage_offers
        )
        if best:
            per_offer[best.id] += ln.line_total * best.value / 100
            names[best.id] = best.name
    discounts = [
        {"offer_id": oid, "label": names[oid], "amount": round_half_up(raw)}
        for oid, raw in per_offer.items()
    ]
    discounts = [d for d in discounts if d["amount"] > 0]
    discount_total = sum((d["amount"] for d in discounts), Decimal("0"))

    # Delivery
    threshold = shop.free_delivery_threshold
    for min_order in (
        Offer.objects.live(now)
        .filter(type=Offer.Type.FREE_DELIVERY, min_order__isnull=False)
        .values_list("min_order", flat=True)
    ):
        threshold = min(threshold, min_order)
    after_discount = subtotal - discount_total
    if not lines:
        delivery_fee = Decimal("0")
    elif after_discount >= threshold:
        delivery_fee = Decimal("0")
    else:
        delivery_fee = shop.delivery_fee
    remaining = max(Decimal("0"), threshold - after_discount)

    return Quote(
        lines=lines,
        subtotal=subtotal,
        discounts=discounts,
        discount_total=discount_total,
        delivery_fee=delivery_fee,
        free_delivery_threshold=threshold,
        free_delivery_remaining=remaining,
        total=after_discount + delivery_fee,
        warnings=warnings,
    )

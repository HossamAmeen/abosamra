"""Live-offer lookups shared by the catalog serializers/filters and the pricing engine."""

from dataclasses import dataclass, field
from decimal import Decimal

from .models import Offer


@dataclass(frozen=True)
class PercentageOffer:
    id: int
    name: str
    value: Decimal
    target_kind: str
    category_id: int | None
    product_ids: frozenset = field(default_factory=frozenset)

    def applies_to(self, product_id: int, category_id: int) -> bool:
        if self.target_kind == Offer.Target.ALL:
            return True
        if self.target_kind == Offer.Target.CATEGORY:
            return self.category_id == category_id
        return product_id in self.product_ids


def live_percentage_offers(now=None) -> list[PercentageOffer]:
    """All live percentage offers in ONE query (targets joined, no prefetch)."""
    rows = (
        Offer.objects.live(now)
        .filter(type=Offer.Type.PERCENTAGE, value__isnull=False)
        .values_list("id", "name", "value", "target_kind", "target_category_id", "target_products")
        .order_by("id")
    )
    grouped: dict[int, dict] = {}
    for oid, name, value, kind, cat_id, product_id in rows:
        entry = grouped.setdefault(
            oid,
            {"name": name, "value": value, "kind": kind, "cat": cat_id, "products": set()},
        )
        if product_id is not None:
            entry["products"].add(product_id)
    return [
        PercentageOffer(oid, e["name"], e["value"], e["kind"], e["cat"], frozenset(e["products"]))
        for oid, e in grouped.items()
    ]


def best_offer_for(product_id, category_id, offers) -> PercentageOffer | None:
    """Highest percentage wins (ties: lowest id) - offers never stack."""
    matching = [o for o in offers if o.applies_to(product_id, category_id)]
    if not matching:
        return None
    return max(matching, key=lambda o: (o.value, -o.id))

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.offers.models import BundleItem, Offer


def percentage_offer(value=15, category=None, products=(), name=None, **kwargs):
    kind = Offer.Target.CATEGORY if category else Offer.Target.PRODUCTS if products else "all"
    offer = Offer.objects.create(
        type=Offer.Type.PERCENTAGE,
        name=name or f"خصم {value}%",
        value=Decimal(value),
        target_kind=kind,
        target_category=category,
        **kwargs,
    )
    if products:
        offer.target_products.set(products)
    return offer


def bundle_offer(variants_qty, price=290, name="باكدج", **kwargs):
    offer = Offer.objects.create(
        type=Offer.Type.BUNDLE, name=name, bundle_price=Decimal(price), **kwargs
    )
    for variant, qty in variants_qty:
        BundleItem.objects.create(offer=offer, variant=variant, qty=qty)
    return offer


def free_delivery_offer(min_order=300, name="توصيل مجاني", **kwargs):
    return Offer.objects.create(
        type=Offer.Type.FREE_DELIVERY, name=name, min_order=Decimal(min_order), **kwargs
    )


def expired(**kwargs):
    return {
        "starts_at": timezone.now() - timedelta(days=10),
        "ends_at": timezone.now() - timedelta(days=1),
        **kwargs,
    }

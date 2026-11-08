"""Idempotent demo data (BSPEC 7). Existing rows are never overwritten, so the owner's edits
survive re-runs; only missing rows are created."""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Category, Product, ProductVariant
from apps.core.models import ShopSettings
from apps.offers.models import BundleItem, Offer
from common.phone import try_normalize_phone

CATEGORIES = [
    ("spices", "بهارات", "#F6D9B8", "soup"),
    ("herbs", "أعشاب ومشروبات", "#DCEBCF", "leaf"),
    ("honey", "عسل وزيوت", "#F9E4A8", "droplet"),
    ("nuts", "مكسرات", "#EBD7C3", "nut"),
    ("grains", "بقوليات وحبوب", "#F2E6C9", "wheat"),
    ("incense", "بخور", "#E6DAEE", "flame"),
]

Q, H, K = "ربع كيلو", "نص كيلو", "كيلو"
# (category, name, featured, [(label, price, compare_at, stock_factor)]); first variant = default
PRODUCTS = [
    (
        "spices", "كمون مطحون", True,
        [(Q, 60, None, "0.25"), (H, 115, None, "0.5"), (K, 220, None, "1")],
    ),
    ("spices", "فلفل أسود حب", False, [(Q, 95, 110, "0.25")]),
    ("spices", "كركم", False, [(Q, 45, None, "0.25")]),
    ("spices", "قرفة عيدان", False, [(Q, 70, None, "0.25")]),
    ("spices", "بهارات مشكلة", False, [(Q, 55, 65, "0.25")]),
    ("herbs", "ينسون", False, [(Q, 50, None, "0.25")]),
    ("herbs", "كركديه", True, [(Q, 65, None, "0.25")]),
    ("herbs", "بابونج", False, [(Q, 40, None, "0.25")]),
    ("herbs", "حبة البركة", False, [(Q, 55, None, "0.25")]),
    ("honey", "عسل نحل طبيعي", True, [(K, 220, 250, "1"), (Q, 60, None, "0.25")]),
    ("honey", "زيت زيتون", False, [("لتر", 280, None, "1")]),
    ("nuts", "لوز مقشر", True, [(Q, 120, None, "0.25")]),
    ("nuts", "كاجو محمص", False, [(Q, 150, 170, "0.25")]),
    ("grains", "عدس أصفر", False, [(K, 60, None, "1")]),
    ("grains", "فريك", False, [(K, 75, None, "1")]),
    ("incense", "بخور عود", False, [("علبة", 90, None, "1")]),
]  # fmt: skip

SPICES_OFFER = "خصم 15% على كل البهارات"
BUNDLE_OFFER = "باكدج الشتا"
FREE_DELIVERY_OFFER = "توصيل مجاني"


def next_thursday_end(now=None):
    """Next Thursday 23:59 in the project time zone (a full week away if today is Thursday)."""
    local = timezone.localtime(now or timezone.now())
    days = (3 - local.weekday()) % 7 or 7
    target = datetime.combine(local.date() + timedelta(days=days), time(23, 59))
    return timezone.make_aware(target, local.tzinfo)


class Command(BaseCommand):
    help = "Create (idempotently) the Abo Samra demo data: settings, catalog, offers, staff user."

    @transaction.atomic
    def handle(self, *args, **options):
        ShopSettings.load()
        categories = self._categories()
        variants = self._products(categories)
        self._offers(categories, variants)
        self._staff()
        self.stdout.write(self.style.SUCCESS("seed_abo_samra: done"))

    def _categories(self):
        result = {}
        for order, (slug, name, color, icon) in enumerate(CATEGORIES, start=1):
            result[slug], _ = Category.objects.get_or_create(
                slug=slug, defaults={"name": name, "color": color, "icon": icon, "order": order}
            )
        return result

    def _products(self, categories):
        variants = {}
        for category, name, featured, rows in PRODUCTS:
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": categories[category],
                    "is_featured": featured,
                },
            )
            if created:
                for index, (label, price, compare_at, factor) in enumerate(rows):
                    ProductVariant.objects.create(
                        product=product,
                        label=label,
                        price=Decimal(price),
                        compare_at_price=Decimal(compare_at) if compare_at else None,
                        stock_factor=Decimal(factor),
                        is_default=index == 0,
                        order=index,
                    )
            for variant in product.variants.all():
                variants[(name, variant.label)] = variant
        return variants

    def _offers(self, categories, variants):
        Offer.objects.get_or_create(
            name=SPICES_OFFER,
            defaults={
                "type": Offer.Type.PERCENTAGE,
                "value": Decimal("15"),
                "target_kind": Offer.Target.CATEGORY,
                "target_category": categories["spices"],
                "ends_at": next_thursday_end(),
                "is_featured": True,
            },
        )
        # NOTE: get_or_create never overwrites existing rows, so a DB seeded earlier keeps its
        # old bundle_price; edit the offer in the admin (or reset the DB) to pick up 160.
        bundle, created = Offer.objects.get_or_create(
            name=BUNDLE_OFFER,
            defaults={"type": Offer.Type.BUNDLE, "bundle_price": Decimal("160")},
        )
        if created:
            for key in (("ينسون", Q), ("كركديه", Q), ("عسل نحل طبيعي", Q)):
                BundleItem.objects.create(offer=bundle, variant=variants[key], qty=1)
            bundle.validate_relations()
        Offer.objects.get_or_create(
            name=FREE_DELIVERY_OFFER,
            defaults={"type": Offer.Type.FREE_DELIVERY, "min_order": Decimal("500")},
        )

    def _staff(self):
        phone = try_normalize_phone(settings.ADMIN_PHONE)
        if not phone or not settings.ADMIN_PASSWORD:
            self.stderr.write(
                "ADMIN_PHONE / ADMIN_PASSWORD not set (or invalid): staff user skipped"
            )
            return
        if User.objects.filter(phone=phone).exists():
            return
        User.objects.create_superuser(
            phone=phone, name=settings.ADMIN_NAME, password=settings.ADMIN_PASSWORD
        )

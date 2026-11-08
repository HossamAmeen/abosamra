from decimal import Decimal

import factory

from apps.catalog.models import Category, Product, ProductVariant


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("slug",)

    slug = factory.Sequence(lambda n: f"cat{n}")
    name = factory.Sequence(lambda n: f"قسم {n}")
    color = "#F6D9B8"
    icon = "soup"
    order = factory.Sequence(lambda n: n)


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"منتج {n}")
    description = "وصف"


class VariantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductVariant

    product = factory.SubFactory(ProductFactory)
    label = "ربع كيلو"
    price = Decimal("60")
    stock_factor = Decimal("1")
    is_default = True


def make_product(name="منتج", price=60, category=None, label="ربع كيلو", **kwargs):
    """Product with one default variant; returns (product, variant)."""
    extra = {"category": category} if category else {}
    product = ProductFactory(name=name, **extra, **kwargs)
    variant = VariantFactory(product=product, price=Decimal(price), label=label)
    return product, variant

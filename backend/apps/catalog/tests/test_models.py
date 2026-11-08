import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from PIL import Image

from apps.catalog.models import Product, ProductVariant

from .factories import CategoryFactory, ProductFactory, VariantFactory

pytestmark = pytest.mark.django_db


def test_unicode_slug_and_clash_suffix():
    p1 = ProductFactory(name="كمون مطحون")
    p2 = ProductFactory(name="كمون مطحون")
    assert p1.slug == "كمون-مطحون"
    assert p2.slug.startswith("كمون-مطحون-") and p2.slug != p1.slug


def test_slug_kept_on_update():
    p = ProductFactory(name="ينسون")
    slug = p.slug
    p.name = "ينسون حب"
    p.save()
    assert p.slug == slug


def test_only_one_default_variant_per_product():
    p = ProductFactory()
    VariantFactory(product=p, is_default=True)
    with pytest.raises(IntegrityError), transaction.atomic():
        VariantFactory(product=p, label="كيلو", is_default=True)
    VariantFactory(product=p, label="كيلو", is_default=False)
    assert p.variants.count() == 2
    assert ProductVariant.objects.filter(product=p, is_default=True).count() == 1


def _jpeg_with_exif(size=(3000, 1500)):
    img = Image.new("RGB", size, "red")
    exif = img.getexif()
    exif[0x010F] = "SecretCamera"  # Make
    exif[0x8825] = {1: "N"}  # GPS IFD
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return SimpleUploadedFile("photo.jpg", buf.getvalue(), content_type="image/jpeg")


def test_image_resized_to_webp_and_exif_stripped():
    original = _jpeg_with_exif()
    assert len(Image.open(io.BytesIO(original.read())).getexif()) > 0
    original.seek(0)
    p = ProductFactory(image=original, category=CategoryFactory())
    p.refresh_from_db()
    assert p.image.name.endswith(".webp")
    with p.image.open("rb") as fh:
        out = Image.open(fh)
        out.load()
        assert out.format == "WEBP"
        assert max(out.size) == 1200
        assert out.size == (1200, 600)
        assert len(out.getexif()) == 0
        assert "exif" not in out.info


def test_small_image_not_upscaled_and_not_reprocessed_on_resave():
    buf = io.BytesIO()
    Image.new("RGB", (200, 100), "blue").save(buf, format="PNG")
    p = ProductFactory(image=SimpleUploadedFile("a.png", buf.getvalue(), content_type="image/png"))
    name = p.image.name
    p.save()
    assert p.image.name == name
    with p.image.open("rb") as fh:
        assert Image.open(fh).size == (200, 100)


def test_product_without_image():
    assert Product.objects.create(category=CategoryFactory(), name="x").image.name in (None, "")

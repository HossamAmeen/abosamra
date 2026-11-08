"""Image pipeline: max 1200 px longest side, WebP, EXIF stripped."""

from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_SIZE = 1200


def process_image(uploaded) -> ContentFile:
    uploaded.seek(0)
    with Image.open(uploaded) as img:
        img = ImageOps.exif_transpose(img)  # apply orientation before EXIF is dropped
        img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "transparency" in img.info else "RGB")
        clean = Image.new(img.mode, img.size)  # fresh image: no EXIF/metadata carried over
        clean.paste(img)
        buffer = BytesIO()
        clean.save(buffer, format="WEBP", quality=85)
    return ContentFile(buffer.getvalue(), name=f"{Path(uploaded.name).stem}.webp")

from django.contrib import admin

from .models import BundleItem, Offer


class BundleItemInline(admin.TabularInline):
    model = BundleItem
    extra = 1


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "is_active", "is_featured", "starts_at", "ends_at")
    list_filter = ("type", "is_active", "is_featured")
    search_fields = ("name",)
    filter_horizontal = ("target_products",)
    inlines = [BundleItemInline]

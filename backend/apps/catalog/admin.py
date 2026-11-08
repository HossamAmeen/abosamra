from django.contrib import admin

from .models import Category, Product, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active")
    list_editable = ("order", "is_active")


class VariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_available", "is_featured", "is_archived", "stock_qty")
    list_filter = ("category", "is_available", "is_featured", "is_archived")
    search_fields = ("name", "description")
    inlines = [VariantInline]

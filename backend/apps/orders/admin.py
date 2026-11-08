from django.contrib import admin

from .models import Order, OrderDiscount, OrderLine, OrderStatusLog


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0
    can_delete = False


class OrderDiscountInline(admin.TabularInline):
    model = OrderDiscount
    extra = 0
    can_delete = False


class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    can_delete = False
    readonly_fields = ("from_status", "to_status", "changed_by", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "status", "total", "created_at")
    list_filter = ("status",)
    search_fields = ("number", "customer__name", "customer__phone")
    readonly_fields = ("number", "status", "created_at", "updated_at")
    inlines = [OrderLineInline, OrderDiscountInline, OrderStatusLogInline]

"""Order creation and the status machine (BSPEC 4.4, 4.5)."""

from collections import defaultdict
from decimal import Decimal

from django.db import connection, transaction
from django.db.models import F, Max
from rest_framework import status as http

from apps.catalog.models import Product, ProductVariant
from apps.core.models import ShopSettings
from common.exceptions import ApiError

from ..models import Order, OrderDiscount, OrderLine, OrderStatusLog
from .notifications import notify_new_order
from .pricing import quote

ORDER_SEQUENCE = "orders_order_number_seq"
FIRST_NUMBER = 1001

TRANSITIONS = {
    Order.Status.NEW: {Order.Status.PREPARING, Order.Status.CANCELLED},
    Order.Status.PREPARING: {Order.Status.OUT_FOR_DELIVERY, Order.Status.CANCELLED},
    Order.Status.OUT_FOR_DELIVERY: {Order.Status.DELIVERED, Order.Status.CANCELLED},
    Order.Status.DELIVERED: set(),
    Order.Status.CANCELLED: set(),
}


def next_order_number() -> int:
    """PostgreSQL: a real sequence (see migration). Other engines (tests): max + 1."""
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("SELECT nextval(%s)", [ORDER_SEQUENCE])
            return cursor.fetchone()[0]
    current = Order.objects.aggregate(m=Max("number"))["m"]
    return FIRST_NUMBER if current is None else max(current + 1, FIRST_NUMBER)


def _stock_usage(q) -> dict[int, Decimal]:
    """product_id -> stock units consumed by the quoted lines (bundle items included)."""
    pairs: list[tuple[int, int]] = []  # (variant_id, qty)
    for line in q.lines:
        if line.variant_id:
            pairs.append((line.variant_id, line.qty))
        elif line.offer is not None:
            pairs.extend((bi.variant_id, bi.qty * line.qty) for bi in line.offer.bundle_items.all())
    variants = {
        v.id: v
        for v in ProductVariant.objects.filter(id__in={p[0] for p in pairs}).select_related(
            "product"
        )
    }
    usage: dict[int, Decimal] = defaultdict(Decimal)
    for variant_id, qty in pairs:
        variant = variants[variant_id]
        if variant.product.stock_qty is not None:  # null = not tracked
            usage[variant.product_id] += variant.stock_factor * qty
    return usage


def cart_changed(q) -> ApiError:
    return ApiError(
        "فيه حاجات في السلة اتغيرت",
        "cart_changed",
        status_code=http.HTTP_409_CONFLICT,
        extra={"quote": q.to_dict()},
    )


def create_order(user, *, items, bundles, address, area="", notes="") -> Order:
    if not ShopSettings.load().is_accepting_orders:
        raise ApiError(
            "المحل مش بياخد طلبات دلوقتي",
            "not_accepting_orders",
            status_code=http.HTTP_503_SERVICE_UNAVAILABLE,
        )
    with transaction.atomic():
        q = quote(items, bundles, for_update=True)
        if q.warnings or not q.lines:
            raise cart_changed(q)

        order = Order.objects.create(
            number=next_order_number(),
            customer=user,
            address=address,
            area=area,
            notes=notes,
            subtotal=q.subtotal,
            discount_total=q.discount_total,
            delivery_fee=q.delivery_fee,
            total=q.total,
        )
        OrderLine.objects.bulk_create(
            OrderLine(
                order=order,
                variant_id=line.variant_id,
                bundle_offer_id=line.offer_id,
                name=line.name,
                unit_label=line.unit_label,
                unit_price=line.unit_price,
                qty=line.qty,
                line_total=line.line_total,
                note=line.note,
            )
            for line in q.lines
        )
        OrderDiscount.objects.bulk_create(
            OrderDiscount(order=order, offer_id=d["offer_id"], label=d["label"], amount=d["amount"])
            for d in q.discounts
        )

        usage = _stock_usage(q)
        for product_id, amount in usage.items():
            Product.objects.filter(pk=product_id).update(stock_qty=F("stock_qty") - amount)
        order.stock_deductions = {str(pid): str(amt) for pid, amt in usage.items()}
        order.save(update_fields=["stock_deductions"])

        OrderStatusLog.objects.create(
            order=order, from_status=None, to_status=Order.Status.NEW, changed_by=user
        )
        user.default_address = address
        user.area = area
        user.save(update_fields=["default_address", "area"])

        transaction.on_commit(lambda: notify_new_order(order))
    return order


def _restore_stock(order: Order) -> None:
    ids = [int(pid) for pid in order.stock_deductions]
    if not ids:
        return
    # Lock the same rows order creation did.
    list(Product.objects.select_for_update().filter(pk__in=ids).values_list("pk", flat=True))
    for pid, amount in order.stock_deductions.items():
        Product.objects.filter(pk=int(pid), stock_qty__isnull=False).update(
            stock_qty=F("stock_qty") + Decimal(amount)
        )
    order.stock_deductions = {}


def change_status(order: Order, to_status: str, by) -> Order:
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)
        if to_status not in TRANSITIONS[order.status]:
            raise ApiError(
                f"مينفعش تغيّر الحالة من {Order.Status(order.status).label} "
                f"لـ {Order.Status(to_status).label}", "invalid_transition"
            )
        previous = order.status
        order.status = to_status
        if to_status == Order.Status.CANCELLED:
            _restore_stock(order)
        order.save()
        OrderStatusLog.objects.create(
            order=order, from_status=previous, to_status=to_status, changed_by=by
        )
    return order

import django_filters
from django.db.models import Exists, OuterRef, Q

from apps.offers.selectors import live_percentage_offers

from .models import Product, ProductVariant


def _truthy(value) -> bool:
    return str(value).lower() in {"true", "1", "yes"}


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method="filter_category")
    q = django_filters.CharFilter(method="filter_q")
    featured = django_filters.CharFilter(method="filter_featured")
    discounted = django_filters.CharFilter(method="filter_discounted")

    class Meta:
        model = Product
        fields: list[str] = []

    def filter_category(self, queryset, name, value):
        if not value or value == "all":
            return queryset
        return queryset.filter(category__slug=value)

    def filter_q(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))

    def filter_featured(self, queryset, name, value):
        return queryset.filter(is_featured=True) if _truthy(value) else queryset

    def filter_discounted(self, queryset, name, value):
        if not _truthy(value):
            return queryset
        has_old_price = Exists(
            ProductVariant.objects.filter(product=OuterRef("pk"), compare_at_price__isnull=False)
        )
        condition = Q(has_old_price=True)
        for offer in live_percentage_offers():
            if offer.target_kind == "all":
                return queryset
            if offer.target_kind == "category":
                condition |= Q(category_id=offer.category_id)
            else:
                condition |= Q(id__in=offer.product_ids)
        return queryset.annotate(has_old_price=has_old_price).filter(condition)

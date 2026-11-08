import django_filters
from django.db.models import Prefetch, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.offers.models import BundleItem
from apps.orders.models import OrderLine

from .admin_serializers import AdminProductSerializer
from .models import Product, ProductVariant


class AdminProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method="filter_category")
    q = django_filters.CharFilter(method="filter_q")
    is_available = django_filters.BooleanFilter()

    class Meta:
        model = Product
        fields: list[str] = []

    def filter_category(self, queryset, name, value):
        if not value or value == "all":
            return queryset
        return (
            queryset.filter(category_id=value)
            if value.isdigit()
            else queryset.filter(category__slug=value)
        )

    def filter_q(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


def admin_products():
    return (
        Product.objects.filter(is_archived=False)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.order_by("-is_default", "order", "id"),
            )
        )
    )


class AdminProductMixin:
    permission_classes = [IsAdminUser]
    serializer_class = AdminProductSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return admin_products().order_by("name", "id")


class AdminProductListView(AdminProductMixin, ListCreateAPIView):
    filterset_class = AdminProductFilter

    @extend_schema(
        parameters=[
            OpenApiParameter("category", str, description="category id or slug"),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminProductDetailView(AdminProductMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "patch", "delete", "head", "options"]
    filter_backends: list = []
    pagination_class = None

    @extend_schema(responses={204: None})
    def delete(self, request, *args, **kwargs):
        """Soft delete (archive + unavailable) when orders reference it, else hard delete."""
        product = self.get_object()
        in_orders = OrderLine.objects.filter(variant__product=product).exists()
        in_bundles = BundleItem.objects.filter(variant__product=product).exists()
        if in_orders or in_bundles:
            product.is_archived = True
            product.is_available = False
            product.save(update_fields=["is_archived", "is_available", "updated_at"])
        else:
            product.delete()
        return Response(status=204)

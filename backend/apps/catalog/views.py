from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from .filters import ProductFilter
from .models import Category, Product, ProductVariant
from .serializers import CategorySerializer, ProductSerializer


class CategoryListView(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    serializer_class = CategorySerializer
    pagination_class = None
    filter_backends: list = []
    queryset = Category.objects.filter(is_active=True).order_by("order", "id")


def public_products():
    """Visible products: not archived, in active categories; variants default-first."""
    return (
        Product.objects.filter(is_archived=False, category__is_active=True)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.order_by("-is_default", "order", "id"),
            )
        )
    )


class ProductListView(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    serializer_class = ProductSerializer
    filterset_class = ProductFilter

    def get_queryset(self):
        return public_products().order_by("-is_featured", "name", "id")

    @extend_schema(operation_id="products_list")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductDetailView(RetrieveAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    serializer_class = ProductSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    filter_backends: list = []
    pagination_class = None

    def get_queryset(self):
        return public_products()

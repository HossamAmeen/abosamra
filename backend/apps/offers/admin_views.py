from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAdminUser

from apps.catalog.models import Product

from .admin_serializers import AdminOfferSerializer
from .models import Offer


class AdminOfferMixin:
    permission_classes = [IsAdminUser]
    serializer_class = AdminOfferSerializer
    filter_backends: list = []
    pagination_class = None  # plain array (leader decision)

    def get_queryset(self):
        return (
            Offer.objects.select_related("target_category")
            .prefetch_related(
                "bundle_items__variant__product",
                Prefetch("target_products", queryset=Product.objects.only("id")),
            )
            .order_by("-created_at", "-id")
        )


class AdminOfferListView(AdminOfferMixin, ListCreateAPIView):
    @extend_schema(responses=AdminOfferSerializer(many=True))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminOfferDetailView(AdminOfferMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "patch", "delete", "head", "options"]

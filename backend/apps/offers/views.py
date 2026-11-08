from django.db.models import Prefetch
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from apps.catalog.models import Product

from .models import Offer
from .serializers import OfferSerializer


class ActiveOfferListView(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    serializer_class = OfferSerializer
    pagination_class = None
    filter_backends: list = []

    def get_queryset(self):
        return (
            Offer.objects.live()
            .select_related("target_category")
            .prefetch_related(
                "bundle_items__variant__product",
                Prefetch("target_products", queryset=Product.objects.only("id")),
            )
            .order_by("-is_featured", "-created_at", "-id")
        )

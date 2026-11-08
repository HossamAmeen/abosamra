from django.urls import path

from .views import ActiveOfferListView

urlpatterns = [
    path("offers/active/", ActiveOfferListView.as_view(), name="offers-active"),
]

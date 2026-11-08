from django.urls import path

from . import admin_views as v

urlpatterns = [
    path("offers/", v.AdminOfferListView.as_view(), name="admin-offer-list"),
    path("offers/<int:pk>/", v.AdminOfferDetailView.as_view(), name="admin-offer-detail"),
]

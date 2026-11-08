from django.urls import path

from . import admin_views as v

urlpatterns = [
    path("products/", v.AdminProductListView.as_view(), name="admin-product-list"),
    path("products/<int:pk>/", v.AdminProductDetailView.as_view(), name="admin-product-detail"),
]

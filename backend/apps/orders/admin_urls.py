from django.urls import path

from . import admin_views as v

urlpatterns = [
    path("dashboard/", v.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("orders/", v.AdminOrderListView.as_view(), name="admin-order-list"),
    path("orders/counts/", v.AdminOrderCountsView.as_view(), name="admin-order-counts"),
    path("orders/<int:pk>/", v.AdminOrderDetailView.as_view(), name="admin-order-detail"),
]

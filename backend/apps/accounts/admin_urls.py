from django.urls import path

from . import admin_views as v

urlpatterns = [
    path("customers/", v.AdminCustomerListView.as_view(), name="admin-customer-list"),
    path(
        "customers/<int:pk>/orders/",
        v.AdminCustomerOrdersView.as_view(),
        name="admin-customer-orders",
    ),
    path("staff/", v.AdminStaffListCreateView.as_view(), name="admin-staff-list"),
    path("me/password/", v.AdminChangePasswordView.as_view(), name="admin-change-password"),
]

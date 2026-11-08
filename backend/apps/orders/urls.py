from django.urls import path

from . import views

urlpatterns = [
    path("cart/quote/", views.CartQuoteView.as_view(), name="cart-quote"),
    path("orders/", views.OrderCreateView.as_view(), name="order-create"),
    path("orders/mine/", views.MyOrdersView.as_view(), name="order-mine"),
    path("orders/<int:pk>/", views.MyOrderDetailView.as_view(), name="order-detail"),
]

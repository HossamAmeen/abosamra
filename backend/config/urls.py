from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from common import messages

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.core.urls_v1")),
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/", include("apps.offers.urls")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/v1/admin/", include("apps.orders.admin_urls")),
    path("api/v1/admin/", include("apps.catalog.admin_urls")),
    path("api/v1/admin/", include("apps.offers.admin_urls")),
    path("api/v1/admin/", include("apps.accounts.admin_urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


def handler404(request, exception=None):
    return JsonResponse({"detail": messages.NOT_FOUND, "code": "not_found"}, status=404)


def handler500(request):
    return JsonResponse({"detail": messages.SERVER_ERROR, "code": "server_error"}, status=500)

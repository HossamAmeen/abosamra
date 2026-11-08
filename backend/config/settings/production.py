from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import INSECURE_DEFAULT_SECRET_KEY, SECRET_KEY, env

DEBUG = False

if SECRET_KEY == INSECURE_DEFAULT_SECRET_KEY or SECRET_KEY.startswith("change-me"):
    raise ImproperlyConfigured("SECRET_KEY must be set to a strong, unique value.")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # required, no default

# Shared cache so throttling works across workers/instances.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("RATELIMIT_CACHE_URL", default="redis://localhost:6379/2"),
    }
}

# Behind Nginx / a load balancer terminating TLS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

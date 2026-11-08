from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-secret-key-0123456789-abcdefghijklmnop"
ALLOWED_HOSTS = ["testserver", "localhost"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
HEALTH_CHECK_PASSWORD = "test-health-password"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
# High defaults so unrelated tests are never throttled; throttle tests lower them.
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {
        **REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],  # noqa: F405
        "anon": "10000/minute",
        "user": "10000/minute",
        "auth": "10000/minute",
        "quote": "10000/minute",
        "orders": "10000/minute",
        "sensitive": "10000/minute",
        "health": "10000/minute",
    },
}

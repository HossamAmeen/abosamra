"""Shared settings. Everything deploy-specific comes from environment variables."""

from datetime import timedelta
from pathlib import Path

import dj_database_url
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(str(_env_file))

INSECURE_DEFAULT_SECRET_KEY = "insecure-dev-key-change-me"
# DJANGO_* names are what deploy/deploy.py writes into the server .env.
SECRET_KEY = env(
    "SECRET_KEY", default=env("DJANGO_SECRET_KEY", default=INSECURE_DEFAULT_SECRET_KEY)
)
DEBUG = env.bool("DEBUG", default=False)
_DEFAULT_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=_DEFAULT_HOSTS)

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # Local
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.offers",
    "apps.orders",
    "apps.backups",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Database: SQLite locally, PostgreSQL in staging/production via DATABASE_URL.
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        default="sqlite:///" + str(BASE_DIR / "db.sqlite3"),
        conn_max_age=600,
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# i18n
LANGUAGE_CODE = "ar"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True

# Static / media
STATIC_URL = "static/"
_STATIC_DEFAULT = env("DJANGO_STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))
STATIC_ROOT = env("STATIC_PATH", default=_STATIC_DEFAULT)
MEDIA_URL = "/media/"
_MEDIA_DEFAULT = env("DJANGO_MEDIA_ROOT", default=str(BASE_DIR / "media"))
MEDIA_ROOT = env("MEDIA_PATH", default=_MEDIA_DEFAULT)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# CORS: only the configured frontend origin(s).
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])
CORS_ALLOW_ALL_ORIGINS = False

# Cache (used by throttling). Overridden with Redis in production.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exception_handler.exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("RATELIMIT_ANON", default="60/minute"),
        "user": env("RATELIMIT_USER", default="300/minute"),
        "auth": env("RATELIMIT_AUTH", default="10/minute"),
        "quote": env("RATELIMIT_QUOTE", default="60/minute"),
        "orders": env("RATELIMIT_ORDERS", default="10/minute"),
        "sensitive": env("RATELIMIT_SENSITIVE", default="30/minute"),
        "health": env("RATELIMIT_HEALTH", default="120/minute"),
    },
}

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=30)
JWT_REFRESH_TOKEN_LIFETIME_DAYS_CUSTOMER = env.int(
    "JWT_REFRESH_TOKEN_LIFETIME_DAYS_CUSTOMER", default=60
)
JWT_REFRESH_TOKEN_LIFETIME_DAYS_STAFF = env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS_STAFF", default=7)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=JWT_ACCESS_TOKEN_LIFETIME_MINUTES),
    # Default (customer) lifetime; staff tokens are shortened in accounts.tokens.
    "REFRESH_TOKEN_LIFETIME": timedelta(days=JWT_REFRESH_TOKEN_LIFETIME_DAYS_CUSTOMER),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Health API
HEALTH_CHECK_PASSWORD = env("HEALTH_CHECK_PASSWORD", default="")

# OpenAPI
SPECTACULAR_SETTINGS = {
    "TITLE": "Abo Samra API",
    "DESCRIPTION": "Backend API for the Abo Samra spice shop store.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# Jazzmin (branding only; not coupled to a business domain)
JAZZMIN_SETTINGS = {
    "site_title": env("ADMIN_SITE_TITLE", default="أبو سمرة"),
    "site_header": env("ADMIN_SITE_HEADER", default="أبو سمرة"),
    "site_brand": env("ADMIN_SITE_BRAND", default="أبو سمرة"),
    "welcome_sign": env("ADMIN_WELCOME_SIGN", default="لوحة التحكم"),
    "copyright": env("ADMIN_SITE_BRAND", default="أبو سمرة"),
    "show_sidebar": True,
    "navigation_expanded": True,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}

# Staff user created by `seed_abo_samra`
ADMIN_PHONE = env("ADMIN_PHONE", default="")
ADMIN_PASSWORD = env("ADMIN_PASSWORD", default="")
ADMIN_NAME = env("ADMIN_NAME", default="أبو سمرة")

# Database backup (`manage.py backup_db`) - see apps/backups and the README
BACKUP_DIR = env("BACKUP_DIR", default=str(BASE_DIR / "backups"))
BACKUP_RETENTION_DAYS = env.int("BACKUP_RETENTION_DAYS", default=7)
BACKUP_TIMEOUT_SECONDS = env.int("BACKUP_TIMEOUT_SECONDS", default=1800)
BACKUP_PG_DUMP_PATH = env("BACKUP_PG_DUMP_PATH", default="pg_dump")
BACKUP_NAME_PREFIX = env("BACKUP_NAME_PREFIX", default="db-backup")
BACKUP_EMAIL_ENABLED = env.bool("BACKUP_EMAIL_ENABLED", default=False)
BACKUP_GOOGLE_DRIVE_ENABLED = env.bool("BACKUP_GOOGLE_DRIVE_ENABLED", default=False)
BACKUP_EMAIL_RECIPIENTS = env.list("BACKUP_EMAIL_RECIPIENTS", default=[])
BACKUP_EMAIL_SUBJECT_PREFIX = env("BACKUP_EMAIL_SUBJECT_PREFIX", default="[Abo Samra]")
BACKUP_EMAIL_MAX_ATTACHMENT_MB = env.int("BACKUP_EMAIL_MAX_ATTACHMENT_MB", default=20)
BACKUP_CRON_HOUR = env.int("BACKUP_CRON_HOUR", default=3)
BACKUP_CRON_MINUTE = env.int("BACKUP_CRON_MINUTE", default=0)

# Email (SMTP) - only used when a feature that sends mail is enabled
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=60)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="")

# Google Drive backup destination
GOOGLE_DRIVE_AUTH_TYPE = env("GOOGLE_DRIVE_AUTH_TYPE", default="service_account")
GOOGLE_DRIVE_FOLDER_ID = env("GOOGLE_DRIVE_FOLDER_ID", default="")
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE = env("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE", default="")
GOOGLE_DRIVE_CLIENT_ID = env("GOOGLE_DRIVE_CLIENT_ID", default="")
GOOGLE_DRIVE_CLIENT_SECRET = env("GOOGLE_DRIVE_CLIENT_SECRET", default="")
GOOGLE_DRIVE_REFRESH_TOKEN = env("GOOGLE_DRIVE_REFRESH_TOKEN", default="")
GOOGLE_DRIVE_RETENTION_DAYS = env.int("GOOGLE_DRIVE_RETENTION_DAYS", default=30)

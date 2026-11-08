"""JWT issuing. Refresh lifetime depends on role: staff 7d, customers 60d."""

from datetime import timedelta

from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


class AppRefreshToken(RefreshToken):
    @property
    def lifetime(self):
        # `payload` does not exist yet while Token.__init__ validates the lifetime.
        payload = getattr(self, "payload", None) or {}
        days = (
            settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS_STAFF
            if payload.get("is_staff")
            else settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS_CUSTOMER
        )
        return timedelta(days=days)

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token["name"] = user.name
        token["is_staff"] = user.is_staff
        token.set_exp(lifetime=token.lifetime)  # recompute now that role is known
        return token


def issue_tokens(user) -> dict:
    refresh = AppRefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}

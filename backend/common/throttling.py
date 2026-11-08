from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle


class AuthRateThrottle(SimpleRateThrottle):
    """Per client IP; used on register + both logins."""

    scope = "auth"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class QuoteRateThrottle(UserRateThrottle):
    """Guests by IP, authenticated users by user id."""

    scope = "quote"


class OrdersRateThrottle(UserRateThrottle):
    """Per user."""

    scope = "orders"


class SensitiveRateThrottle(UserRateThrottle):
    scope = "sensitive"


class HealthRateThrottle(SimpleRateThrottle):
    scope = "health"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}

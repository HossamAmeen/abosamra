from rest_framework import status
from rest_framework.exceptions import APIException


class ApiError(APIException):
    """Application error rendered as {"detail", "code", **extra}."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail, code, status_code=None, extra=None):
        super().__init__(detail=detail, code=code)
        if status_code is not None:
            self.status_code = status_code
        self.extra = extra or {}

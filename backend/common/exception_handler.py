"""Centralized exception handling.

Emits `{"detail": "...", "code": "..."}` for every non-validation error
(401/403/404/405/429/5xx ...). Validation errors keep DRF's default
`{"field": ["..."]}` shape.
"""

import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from common import messages
from common.exceptions import ApiError

logger = logging.getLogger(__name__)

# code -> Egyptian Arabic message (overrides DRF's translated defaults)
MESSAGES = {
    "not_authenticated": messages.NOT_AUTHENTICATED,
    "authentication_failed": messages.AUTHENTICATION_FAILED,
    "token_not_valid": messages.TOKEN_INVALID,
    "permission_denied": messages.PERMISSION_DENIED,
    "not_found": messages.NOT_FOUND,
    "method_not_allowed": messages.METHOD_NOT_ALLOWED,
    "parse_error": messages.PARSE_ERROR,
    "unsupported_media_type": messages.UNSUPPORTED_MEDIA_TYPE,
    "not_acceptable": messages.NOT_ACCEPTABLE,
    "throttled": messages.THROTTLED,
    "error": messages.SERVER_ERROR,
}


def error_body(detail, code, **extra):
    return {"detail": detail, "code": code, **extra}


def exception_handler(exc, context):
    if isinstance(exc, ApiError):
        return Response(
            error_body(str(exc.detail), exc.detail.code, **exc.extra),
            status=exc.status_code,
        )

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled exception", exc_info=exc)
        return Response(
            error_body(messages.SERVER_ERROR, "server_error"),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, exceptions.ValidationError):
        return response

    if isinstance(exc, exceptions.APIException):
        data = response.data
        # simplejwt style: {"detail": ..., "code": ..., "messages": [...]}
        if isinstance(data, dict) and "code" in data:
            code = str(data["code"])
        else:
            code = exc.get_codes()
            code = code if isinstance(code, str) else getattr(exc, "default_code", "error")
        detail = MESSAGES.get(code)
        if detail is None:
            raw = data.get("detail") if isinstance(data, dict) else data
            detail = str(raw)
        if isinstance(exc, exceptions.AuthenticationFailed) and code == "authentication_failed":
            detail = MESSAGES["authentication_failed"]
        response.data = error_body(detail, code)
    return response

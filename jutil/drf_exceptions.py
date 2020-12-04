import logging
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def transform_exception_to_drf(exception: Exception) -> Exception:
    """
    Transform Django ValidationError into an equivalent DRF ValidationError.
    Note that even if this approach is not technically recommended, this is still
    the most convenient way to handle shared validation between Django admin and API.
    """
    if isinstance(exception, DjangoValidationError):
        detail: Any = str(exception)
        if hasattr(exception, "message_dict"):
            detail = exception.message_dict
        elif hasattr(exception, "messages"):
            detail = exception.messages
        elif hasattr(exception, "message"):
            detail = exception.message
        else:
            logger.error("Unsupported ValidationError detail: %s", exception)
        return DRFValidationError(detail=detail)
    return exception


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler which converts Django ValidationError to DRF ValidationError.
    Note that even if this approach is not technically recommended, this is still
    the most convenient way to handle shared validation between Django admin and API.

    DRF exception handler must be set in settings.py:

    REST_FRAMEWORK = {
    ...     # ...
    ...     'EXCEPTION_HANDLER': 'jutil.drf_exceptions.custom_exception_handler',
    ...     # ...
    ... }
    """
    if isinstance(exc, DjangoValidationError):
        exc = transform_exception_to_drf(exc)
    return drf_exception_handler(exc, context)

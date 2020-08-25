import logging
from typing import Union, Optional
from django.contrib.auth.models import User
from django.http.request import HttpRequest
from rest_framework.exceptions import NotAuthenticated
from rest_framework.request import Request

logger = logging.getLogger(__name__)


def get_auth_user(request: Union[Request, HttpRequest]) -> User:
    """
    Returns authenticated User.
    :param request: HttpRequest
    :return: User
    """
    if not request.user or not request.user.is_authenticated:
        raise NotAuthenticated()
    return request.user  # type: ignore


def get_auth_user_or_none(request: Union[Request, HttpRequest]) -> Optional[User]:
    """
    Returns authenticated User or None if not authenticated.
    :param request: HttpRequest
    :return: User
    """
    if not request.user or not request.user.is_authenticated:
        return None
    return request.user  # type: ignore


class AuthUserMixin:
    @property
    def auth_user(self) -> User:
        """
        Returns authenticated user.
        :return: User
        """
        return get_auth_user(self.request)  # type: ignore

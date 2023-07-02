import logging
from typing import Optional
from uuid import uuid1
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

logger = logging.getLogger(__name__)


class TestSetupMixin:
    @staticmethod
    def add_test_user(email: str = "", password: str = "", username: str = "", **kwargs) -> User:  # nosec
        """
        Add and login test user.
        :param email: Optional email. Default is <random>@example.com
        :param password: Optional password. Default is <random>.
        :param username: Optional username. Defaults to email.
        :return: User
        """
        if not email:
            email = "{}@example.com".format(username or uuid1().hex)
        if not password:
            email = email.split("@")[0]
        if not username:
            username = email
        user = get_user_model().objects.create(username=username, email=email, **kwargs)
        user.set_password(password)
        user.save()
        return user

    @staticmethod
    def create_api_client(user: Optional[User] = None) -> APIClient:
        """
        Creates APIClient with optionally authenticated user (by authorization token).
        :param user: User to authenticate (optional)
        :return: APIClient
        """
        token: Optional[Token] = None
        if user:
            token = Token.objects.get_or_create(user=user)[0]
            assert isinstance(token, Token)
        api_client = APIClient()
        if token:
            api_client.credentials(HTTP_AUTHORIZATION="Token {}".format(token.key))
        return api_client

import logging
import traceback
from typing import Dict, Optional
from urllib.parse import urlencode
from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone
from ipware import get_client_ip  # type: ignore
from jutil.email import send_email

logger = logging.getLogger(__name__)


class EnsureOriginMiddleware:
    """
    Ensures that request META 'HTTP_ORIGIN' is set.
    Uses request get_host() to set it if missing.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if not request.META.get("HTTP_ORIGIN", None):
            request.META["HTTP_ORIGIN"] = request.get_host()

        # get response
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response


class LogExceptionMiddleware:
    """
    Logs exception and sends email to admins about it.
    Uses list of emails from settings.ADMINS.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, e):
        """
        Logs exception error message and sends email to ADMINS if hostname is not testserver and DEBUG=False.
        :param request: HttpRequest
        :param e: Exception
        """
        assert isinstance(request, HttpRequest)
        method = str(request.method).upper()
        uri = request.build_absolute_uri()
        user = request.user
        msg = "{method} {uri}\n{err} (IP={ip}, user={user}) {trace}".format(
            method=method, uri=uri, user=user, ip=get_client_ip(request)[0], err=e, trace=traceback.format_exc()
        )
        logger.error(msg)
        hostname = request.get_host()
        if not settings.DEBUG and hostname != "testserver":
            send_email(settings.ADMINS, "Error @ {}".format(hostname), msg)


class EnsureLanguageCookieMiddleware:
    """
    Ensures language cookie (by name settings.LANGUAGE_COOKIE_NAME) is set.
    Sets it as settings.LANGUAGE_CODE if missing.
    Allows changing settings by passing querystring parameter named settings.LANGUAGE_COOKIE_NAME
    (default: django_language).

    Order of preference for the language (must be one of settings.LANGUAGES to be used):
    1) Explicit querystring GET parameter (e.g. ?lang=en)
    2) Previously stored cookie
    3) settings.LANGUAGE_CODE
    """

    _languages: Optional[Dict[str, str]]

    def __init__(self, get_response=None):
        self.get_response = get_response
        self._languages = None

    @property
    def languages(self) -> Dict[str, str]:
        if self._languages is None:
            self._languages = dict(settings.LANGUAGES)
        return self._languages

    def __call__(self, request):
        lang_cookie_name = settings.LANGUAGE_COOKIE_NAME if hasattr(settings, "LANGUAGE_COOKIE_NAME") else "django_language"
        lang_cookie = request.COOKIES.get(lang_cookie_name)
        lang = request.GET.get(lang_cookie_name)
        if not lang:
            lang = lang_cookie
        if not lang or lang not in self.languages:
            lang = settings.LANGUAGE_CODE if hasattr(settings, "LANGUAGE_CODE") else "en"
        request.COOKIES[lang_cookie_name] = lang

        res = self.get_response(request)

        if lang_cookie is None or lang != lang_cookie:
            secure = hasattr(settings, "LANGUAGE_COOKIE_SECURE") and settings.LANGUAGE_COOKIE_SECURE
            httponly = hasattr(settings, "LANGUAGE_COOKIE_HTTPONLY") and settings.LANGUAGE_COOKIE_HTTPONLY
            res.set_cookie(lang_cookie_name, lang, secure=secure, httponly=httponly)
        return res


class ActivateUserProfileTimezoneMiddleware:
    """
    Uses 'timezone' string in request.user.profile to activate user-specific timezone.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        activated = False
        if request.user.is_authenticated:
            user = request.user
            if hasattr(user, "profile") and user.profile:
                up = user.profile
                if hasattr(up, "timezone") and up.timezone:
                    timezone.activate(up.timezone)
                    activated = True
                else:
                    logger.warning("User profile timezone missing so user.profile.timezone could not be activated")
            else:
                logger.warning("User profile missing so user.profile.timezone could not be activated")

        # get response
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        if activated:
            timezone.deactivate()
        return response


class TestClientLoggerMiddleware:
    """
    Logs requests to be used with Django test framework client.
    """

    ignored_paths = {
        "/admin/jsi18n/",
        "/favicon.ico",
    }

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG:
            assert isinstance(request, HttpRequest)
            if request.path not in self.ignored_paths:
                url = request.path
                qs = request.GET.dict()
                if qs:
                    url += "?" + urlencode(request.GET.dict())
                logger.debug('self.client.%s("%s", data=%s)', request.method.lower(), url, request.POST.dict())
        response = self.get_response(request)
        return response

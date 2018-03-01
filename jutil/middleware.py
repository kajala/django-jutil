import logging
import traceback
from django.conf import settings
from django.http import HttpRequest
from ipware.ip import get_real_ip


logger = logging.getLogger(__name__)


class EnsureOriginMiddleware(object):
    """
    Ensures that META HTTP_ORIGIN is set.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        hostname = request.get_host()
        if not request.META.get('HTTP_ORIGIN', None):
            request.META['HTTP_ORIGIN'] = hostname

        # get response
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        return response


class LogExceptionMiddleware(object):
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
        from jutil.email import send_email

        assert isinstance(request, HttpRequest)
        full_path = request.get_full_path()
        user = request.user
        msg = '{full_path}\n{err} (IP={ip}, user={user}) {trace}'.format(full_path=full_path, user=user, ip=get_real_ip(request), err=e, trace=str(traceback.format_exc()))
        logger.error(msg)
        hostname = request.get_host()
        if not settings.DEBUG and hostname != 'testserver':
            send_email(settings.ADMINS, 'Error @ {}'.format(hostname), msg)
        return None


class EnsureLanguageCookieMiddleware(object):
    """
    Ensures language cookie (by name settings.LANGUAGE_COOKIE_NAME) is set.
    Sets it as settings.LANGUAGE_CODE if missing.
    Allows changing settings by passing querystring parameter named settings.LANGUAGE_COOKIE_NAME
    (default: django_language).
    """
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        lang_cookie_name = settings.LANGUAGE_COOKIE_NAME if hasattr(settings, 'LANGUAGE_COOKIE_NAME') else 'django_language'
        lang_cookie = request.COOKIES.get(lang_cookie_name)
        lang = request.GET.get(lang_cookie_name)
        if not lang:
            lang = lang_cookie
        if not lang or lang not in [lang[0] for lang in settings.LANGUAGES]:
            lang = settings.LANGUAGE_CODE if hasattr(settings, 'LANGUAGE_CODE') else 'en'
        request.COOKIES[lang_cookie_name] = lang

        res = self.get_response(request)
        if request.COOKIES[lang_cookie_name] != lang_cookie:
            res.set_cookie(lang_cookie_name, lang)
        return res

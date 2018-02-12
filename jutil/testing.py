import json
from datetime import datetime, timedelta
from os.path import join
from pprint import pprint
import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.timezone import now
from jutil.request import get_ip_info
from jutil.urls import url_equals, url_mod, url_host
from jutil.xml import xml_to_dict, dict_to_element
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from jutil.dates import add_month, per_delta, per_month
from jutil.format import format_full_name, format_xml
from jutil.parse import parse_datetime
from jutil.validators import fi_payment_reference_number, se_ssn_validator, se_ssn_filter, fi_iban_validator, \
    se_iban_validator, iban_filter_readable, email_filter


class DefaultTestSetupMixin(object):
    user = None
    token = None
    api_client = None
    verbose = True

    def debug_print(self, *args, **kw):
        if kw.pop('verbose', self.verbose):
            print(*args)

    def request(self, method: str, path: str, data: dict, **kw) -> (dict, int):
        verbose = kw.pop('verbose', self.verbose)
        self.debug_print('HTTP {} {} {}'.format(method.upper(), path, data), verbose=verbose)
        # print('HTTP {method} {data}'.format(method=method.upper(), data=data))
        # res = getattr(self.api_client, method.lower())(path, data=data)
        res = getattr(self.api_client, method.lower())(path, data=json.dumps(data), content_type='application/json')
        reply = res.json()
        self.debug_print('HTTP {} {} {}: {}'.format(method.upper(), res.status_code, path, reply), verbose=verbose)
        return reply, res.status_code

    def post(self, path: str, data: dict, **kw) -> dict:
        reply, status_code = self.request('post', path, data, **kw)
        if status_code >= 300:
            raise Exception('HTTP {} {} {}: {} {}'.format('POST', status_code, path, data, reply))
        return reply

    def get(self, path: str, data: dict, **kw) -> dict:
        reply, status_code = self.request('get', path, data, **kw)
        if status_code >= 300:
            raise Exception('HTTP {} {} {}: {} {}'.format('GET', status_code, path, data, reply))
        return reply

    def put(self, path: str, data: dict, **kw) -> dict:
        reply, status_code = self.request('put', path, data, **kw)
        if status_code >= 300:
            raise Exception('HTTP {} {} {}: {} {}'.format('PUT', status_code, path, data, reply))
        return reply

    def patch(self, path: str, data: dict, **kw) -> dict:
        reply, status_code = self.request('patch', path, data, **kw)
        if status_code >= 300:
            raise Exception('HTTP {} {} {}: {} {}'.format('PATCH', status_code, path, data, reply))
        return reply

    def delete(self, path: str, data: dict, **kw) -> dict:
        reply, status_code = self.request('delete', path, data, **kw)
        if status_code >= 300:
            raise Exception('HTTP {} {} {}: {} {}'.format('DELETE', status_code, path, data, reply))
        return reply

    def add_test_user(self, email: str='test@example.com', password: str='test1234'):
        """
        Add and login test user.
        :param email:
        :param password:
        :return:
        """
        self.user = User.objects.create_user(email, email, password)
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION='Token {}'.format(self.token.key))

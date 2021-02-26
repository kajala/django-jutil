import logging
from typing import Tuple, Union
from django.conf import settings
import requests
import socket
from django.http.request import HttpRequest
from ipware import get_client_ip  # type: ignore
from rest_framework.request import Request


logger = logging.getLogger(__name__)


def get_ip(request: Union[HttpRequest, Request]) -> str:
    """
    Returns best-guess IP for given request.
    Uses ipware library get_client_ip.
    If you need to know is IP routable or not, use ipware get_client_ip directly.
    See ipware documentation for more info.

    Note: Why such a simple function wrapper? I'm generally against wrappers like this,
    but in this case made an exceptions: I used to use ipware get_real_ip() everywhere before
    it was deprecated and had quite big update process to change all code to use ipware get_client_ip.
    I want to avoid such process again so added this wrapper.

    :param request: Djangos HttpRequest or DRF Request
    :return: IP-address or None
    """
    return get_client_ip(request)[0]


def get_geo_ip(ip: str, exceptions: bool = False, timeout: int = 10) -> dict:
    """
    Returns geo IP info or empty dict if geoip query fails at http://ipstack.com.
    requires settings.IPSTACK_TOKEN set as valid access token to the API.

    Example replies:

    {'country_name': 'United States', 'country_code': 'US', 'region_code': 'TX', 'region_name': 'Texas',
    'ip': '76.184.236.184', 'latitude': 33.1507, 'time_zone': 'America/Chicago', 'metro_code': 623, 'city':
    'Frisco', 'longitude': -96.8236, 'zip_code': '75033'}

    {'latitude': 60.1641, 'country_name': 'Finland', 'zip_code': '02920', 'region_name': 'Uusimaa', 'city':
    'Espoo', 'metro_code': 0, 'ip': '194.100.27.41', 'time_zone': 'Europe/Helsinki', 'country_code': 'FI',
    'longitude': 24.7136, 'region_code': '18'}

    :param ip: str
    :param exceptions: if True raises Exception on failure
    :param timeout: timeout in seconds
    :return: dict
    """
    try:
        if not hasattr(settings, "IPSTACK_TOKEN") or not settings.IPSTACK_TOKEN:
            raise Exception("get_geo_ip() requires IPSTACK_TOKEN defined in Django settings")
        res = requests.get(
            "http://api.ipstack.com/{}?access_key={}&format=1".format(ip, settings.IPSTACK_TOKEN), timeout=timeout
        )
        if res.status_code != 200:
            raise Exception("api.ipstack.com HTTP {}".format(res.status_code))
        return res.json()
    except Exception as e:
        msg = "geoip({}) failed: {}".format(ip, e)
        logger.error(msg)
        if exceptions:
            raise
        return {}


def get_ip_info(ip: str, exceptions: bool = False, timeout: int = 10) -> Tuple[str, str, str]:
    """
    Returns (ip, country_code, host) tuple of the IP address.
    :param ip: IP address
    :param exceptions: Raise Exception or not
    :param timeout: Timeout in seconds. Note that timeout only affects geo IP part, not getting host name.
    :return: (ip, country_code, host)
    """
    if not ip:  # localhost
        return "", "", ""
    host = ""
    country_code = get_geo_ip(ip, exceptions=exceptions, timeout=timeout).get("country_code", "")
    try:
        res = socket.gethostbyaddr(ip)
        host = res[0][:255] if ip else ""
    except Exception as e:
        msg = "socket.gethostbyaddr({}) failed: {}".format(ip, e)
        logger.error(msg)
        if exceptions:
            raise e
    return ip, country_code, host

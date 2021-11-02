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


def get_geo_ip_from_ipgeolocation(ip: str, exceptions: bool = False, timeout: int = 10) -> dict:
    """
    Returns geo IP info or empty dict if geoip query fails.
    Uses ipgeolocation.io API and requires settings.IPGEOLOCATION_API_KEY set.

    Example replies:

        {
            "ip": "76.184.236.184",
            "continent_code": "NA",
            "continent_name": "North America",
            "country_code2": "US",
            "country_code3": "USA",
            "country_name": "United States",
            "country_capital": "Washington, D.C.",
            "state_prov": "Texas",
            "district": "Collin",
            "city": "Frisco",
            "zipcode": "75034",
            "latitude": "33.15048",
            "longitude": "-96.83466",
            "is_eu": false,
            "calling_code": "+1",
            "country_tld": ".us",
            "languages": "en-US,es-US,haw,fr",
            "country_flag": "https://ipgeolocation.io/static/flags/us_64.png",
            "geoname_id": "9686447",
            "isp": "Charter Communications Inc",
            "connection_type": "",
            "organization": "Charter Communications Inc",
            "currency": {
                "code": "USD",
                "name": "US Dollar",
                "symbol": "$"
            },
            "time_zone": {
                "name": "America/Chicago",
                "offset": -6,
                "current_time": "2021-11-02 11:04:25.432-0500",
                "current_time_unix": 1635869065.432,
                "is_dst": true,
                "dst_savings": 1
            }
        }

        {
            "ip": "194.100.27.41",
            "continent_code": "EU",
            "continent_name": "Europe",
            "country_code2": "FI",
            "country_code3": "FIN",
            "country_name": "Finland",
            "country_capital": "Helsinki",
            "state_prov": "South Finland",
            "district": "",
            "city": "Helsinki",
            "zipcode": "00100",
            "latitude": "60.17116",
            "longitude": "24.93265",
            "is_eu": true,
            "calling_code": "+358",
            "country_tld": ".fi",
            "languages": "fi-FI,sv-FI,smn",
            "country_flag": "https://ipgeolocation.io/static/flags/fi_64.png",
            "geoname_id": "6473658",
            "isp": "DNA Oyj",
            "connection_type": "",
            "organization": "DNA Oyj",
            "currency": {
                "code": "EUR",
                "name": "Euro",
                "symbol": "\u20ac"
            },
            "time_zone": {
                "name": "Europe/Helsinki",
                "offset": 2,
                "current_time": "2021-11-02 18:05:08.327+0200",
                "current_time_unix": 1635869108.327,
                "is_dst": false,
                "dst_savings": 1
            }
        }

    :param ip: str
    :param exceptions: if True raises Exception on failure
    :param timeout: timeout in seconds
    :return: dict
    """
    try:
        if not hasattr(settings, "IPGEOLOCATION_API_KEY") or not settings.IPGEOLOCATION_API_KEY:
            raise Exception("get_geo_ip_ipstack() requires IPGEOLOCATION_API_KEY defined in Django settings")
        res = requests.get(f"https://api.ipgeolocation.io/ipgeo?apiKey={settings.IPGEOLOCATION_API_KEY}&ip={ip}", timeout=timeout)
        if res.status_code != 200:
            raise Exception("api.ipgeolocation.io HTTP {}".format(res.status_code))
        data = res.json()
        return data
    except Exception as e:
        logger.error("get_geo_ip_from_ipgeolocation(%s) failed: %s", ip, e)
        if exceptions:
            raise
        return {}


def get_geo_ip_from_ipstack(ip: str, exceptions: bool = False, timeout: int = 10) -> dict:
    """
    Returns geo IP info or empty dict if geoip query fails.
    Uses ipstack.com API and requires settings.IPSTACK_TOKEN set.

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
            raise Exception("get_geo_ip_from_ipstack() requires IPSTACK_TOKEN defined in Django settings")
        res = requests.get(f"http://api.ipstack.com/{ip}?access_key={settings.IPSTACK_TOKEN}&format=1", timeout=timeout)
        if res.status_code != 200:
            raise Exception("api.ipstack.com HTTP {}".format(res.status_code))
        data = res.json()
        res_success = data.get("success", True)
        if not res_success:
            res_info = data.get("info") or ""
            raise Exception(res_info)
        return data
    except Exception as e:
        logger.error("get_geo_ip_from_ipstack(%s) failed: %s", ip, e)
        if exceptions:
            raise
        return {}


def get_geo_ip(ip: str, exceptions: bool = False, timeout: int = 10) -> dict:
    """
    Returns geo IP info or empty dict if geoip query fails.
    Uses either ipgeolocation.io (if IPGEOLOCATION_TOKEN set) or ipstack.com (if IPSTACK_TOKEN set)

    :param ip: str
    :param exceptions: if True raises Exception on failure
    :param timeout: timeout in seconds
    :return: dict
    """
    if hasattr(settings, "IPGEOLOCATION_API_KEY") and settings.IPGEOLOCATION_API_KEY:
        return get_geo_ip_from_ipgeolocation(ip, exceptions, timeout)
    if hasattr(settings, "IPSTACK_TOKEN") and settings.IPSTACK_TOKEN:
        return get_geo_ip_from_ipstack(ip, exceptions, timeout)
    raise Exception("get_geo_ip() requires either IPGEOLOCATION_TOKEN or IPSTACK_TOKEN defined in Django settings")


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
    data = get_geo_ip(ip, exceptions=exceptions, timeout=timeout)
    country_code = str(data.get("country_code2") or data.get("country_code") or "")
    try:
        res = socket.gethostbyaddr(ip)
        host = res[0][:255] if ip else ""
    except Exception as e:
        logger.error("socket.gethostbyaddr(%s) failed: %s", ip, e)
        if exceptions:
            raise e
    return ip, country_code, host

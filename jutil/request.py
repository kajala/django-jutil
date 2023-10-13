import logging
from typing import Tuple, Optional
from django.conf import settings
import requests
import socket
from ipware import get_client_ip  # type: ignore

logger = logging.getLogger(__name__)


class GeoIP:
    """
    Basic geolocation information of IP-address.
    """

    ip: str
    country_name: str
    country_code: str
    time_zone: str
    city: str
    zip_code: str
    latitude: float
    longitude: float

    def __init__(  # pylint: disable=too-many-arguments
        self,
        ip: str,
        country_name: str,
        country_code: str,
        time_zone: str,
        city: str,
        zip_code: str,
        latitude: float,
        longitude: float,
    ):
        self.ip = ip
        self.country_name = country_name
        self.country_code = country_code
        self.time_zone = time_zone
        self.city = city
        self.zip_code = zip_code
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return f"{self.ip} ({self.country_code})"


def get_ip(request) -> str:
    """Returns best-guess IP for given request.
    Uses ipware library get_client_ip.
    If you need to know is IP routable or not, use ipware get_client_ip directly.
    See ipware documentation for more info.

    Note: Why such a simple function wrapper? I'm generally against wrappers like this,
    but in this case made an exceptions: I used to use ipware get_real_ip() everywhere before
    it was deprecated and had quite big update process to change all code to use ipware get_client_ip.
    I want to avoid such process again so added this wrapper.

    Args:
        request: Django's HttpRequest or DRF Request

    Returns:
        IP-address or None
    """
    return get_client_ip(request)[0]


def get_geo_ip_from_ipgeolocation(ip: str, timeout: int = 10, verbose: bool = False) -> GeoIP:
    """Returns geo IP info or empty dict if geoip query fails.
    Uses ipgeolocation.io API and requires settings.IPGEOLOCATION_API_KEY set.

    Args:
        ip: str
        timeout: timeout in seconds

    Returns:
        IPGeoInfo
    """
    if not hasattr(settings, "IPGEOLOCATION_API_KEY") or not settings.IPGEOLOCATION_API_KEY:
        raise Exception("get_geo_ip_ipstack() requires IPGEOLOCATION_API_KEY defined in Django settings")  # noqa
    url = f"https://api.ipgeolocation.io/ipgeo?apiKey={settings.IPGEOLOCATION_API_KEY}&ip={ip}"
    res = requests.get(url, timeout=timeout)
    if verbose:
        logger.info("GET %s HTTP %s: %s", url, res.status_code, res.text)
    if res.status_code != 200:
        logger.error("get_geo_ip_from_ipgeolocation(%s) failed: %s", ip, res.text)
        raise Exception("api.ipgeolocation.io HTTP {}".format(res.status_code))  # noqa
    data = res.json()
    return GeoIP(
        ip,
        country_name=data["country_name"],
        country_code=data["country_code2"],
        time_zone=(data.get("time_zone") or {}).get("name") or "",
        city=data.get("city") or "",
        zip_code=data.get("zipcode") or "",
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
    )


def get_geo_ip_from_ipstack(ip: str, timeout: int = 10, verbose: bool = False) -> GeoIP:
    """Returns geo IP info or empty dict if geoip query fails.
    Uses ipstack.com API and requires settings.IPSTACK_TOKEN set.

    Args:
        ip: str
        timeout: timeout in seconds

    Returns:
        IPGeoInfo
    """
    if not hasattr(settings, "IPSTACK_TOKEN") or not settings.IPSTACK_TOKEN:
        raise Exception("get_geo_ip_from_ipstack() requires IPSTACK_TOKEN defined in Django settings")  # noqa
    url = f"http://api.ipstack.com/{ip}?access_key={settings.IPSTACK_TOKEN}&format=1"
    res = requests.get(url, timeout=timeout)
    if verbose:
        logger.info("GET %s HTTP %s: %s", url, res.status_code, res.text)
    if res.status_code != 200:
        logger.error("get_geo_ip_from_ipstack(%s) failed: %s", ip, res.text)
        raise Exception("api.ipstack.com HTTP {}".format(res.status_code))  # noqa
    data = res.json()
    res_success = data.get("success", True)
    if not res_success:
        res_info = data.get("info") or ""
        logger.error("get_geo_ip_from_ipstack(%s) failed: %s", ip, res_info)
        raise Exception(res_info)  # noqa
    return GeoIP(
        ip,
        country_name=data["country_name"],
        country_code=data["country_code"],
        time_zone=data.get("time_zone") or "",
        city=data.get("city") or "",
        zip_code=data.get("zip") or "",
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
    )


def get_geo_ip(ip: str, timeout: int = 10, verbose: bool = False) -> GeoIP:
    """Returns geo IP info. Raises Exception if query fails.
    Uses either ipgeolocation.io (if IPGEOLOCATION_API_KEY set) or ipstack.com (if IPSTACK_TOKEN set)

    Example response (GeoIP.__dict__):

            {
                "ip": "194.100.27.41",
                "country_name": "Finland",
                "country_code": "FI",
                "time_zone": "Europe/Helsinki",
                "city": "Helsinki",
                "zip_code": "00100",
                "latitude": "60.17116",
                "longitude": "24.93265"
            }

    Args:
        ip: str
        timeout: timeout in seconds

    Returns:
        IPGeoInfo
    """
    if hasattr(settings, "IPGEOLOCATION_API_KEY") and settings.IPGEOLOCATION_API_KEY:
        return get_geo_ip_from_ipgeolocation(ip, timeout, verbose=verbose)
    if hasattr(settings, "IPSTACK_TOKEN") and settings.IPSTACK_TOKEN:
        return get_geo_ip_from_ipstack(ip, timeout, verbose=verbose)
    raise Exception("get_geo_ip() requires either IPGEOLOCATION_TOKEN or IPSTACK_TOKEN defined in Django settings")  # noqa


def get_geo_ip_or_none(ip: str, timeout: int = 10) -> Optional[GeoIP]:
    """Returns geo IP info or None if geoip query fails.
    Uses either ipgeolocation.io (if IPGEOLOCATION_API_KEY set) or ipstack.com (if IPSTACK_TOKEN set)

    Args:
        ip: str
        timeout: timeout in seconds

    Returns:
        Optional[IPGeoInfo]
    """
    try:
        return get_geo_ip(ip, timeout)
    except Exception as err:
        logger.error("get_geo_ip_or_none(%s) failed: %s", ip, err)
    return None


def get_ip_info(ip: str, exceptions: bool = False, timeout: int = 10) -> Tuple[str, str, str]:
    """Returns (ip, country_code, host) tuple of the IP address.
    Uses either ipgeolocation.io (if IPGEOLOCATION_API_KEY set) or ipstack.com (if IPSTACK_TOKEN set)

    Args:
        ip: IP address
        exceptions: Raise Exception or not
        timeout: Timeout in seconds. Note that timeout only affects geo IP part, not getting host name.

    Returns:
        (ip, country_code, host)
    """
    if not ip:  # localhost
        return "", "", ""
    host, country_code = "", ""
    try:
        geo = get_geo_ip(ip, timeout=timeout)
        country_code = geo.country_code
        if ip:
            host_info = socket.gethostbyaddr(ip)
            host = host_info[0][:255]
    except Exception as e:
        logger.error("get_ip_info(%s) failed: %s", ip, e)
        if exceptions:
            raise e
    return ip, country_code, host

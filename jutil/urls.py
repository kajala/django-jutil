import logging
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode

logger = logging.getLogger(__name__)


def modify_url(url: str, new_params: dict) -> str:
    """
    Modifies existing URL by setting/overriding specified query string parameters.
    This can be useful for example if you need to modify user-provided callback URL
    for extra arguments. Note: Does not support multiple querystring parameters with identical name.
    :param url: Base URL/path to modify
    :param new_params: Querystring parameters to set/override (dict)
    :return: New URL/path
    """
    res = urlparse(url)
    query_params = dict(parse_qsl(res.query))
    for k, v in new_params.items():
        if v is None:
            query_params[str(k)] = ""
        else:
            query_params[str(k)] = str(v)
    parts = list(res)
    parts[4] = urlencode(query_params)
    return urlunparse(parts)

from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode


def url_equals(a: str, b: str) -> bool:
    """
    Compares two URLs/paths and returns True if they point to same URI.
    For example, querystring parameters can be different order but URLs are still equal.
    :param a: URL/path
    :param b: URL/path
    :return: True if URLs/paths are equal
    """
    a2 = list(urlparse(a))
    b2 = list(urlparse(b))
    a2[4] = dict(parse_qsl(a2[4]))  # type: ignore
    b2[4] = dict(parse_qsl(b2[4]))  # type: ignore
    return a2 == b2


def url_mod(url: str, new_params: dict) -> str:
    """
    Modifies existing URL by setting/overriding specified query string parameters.
    Note: Does not support multiple querystring parameters with identical name.
    :param url: Base URL/path to modify
    :param new_params: Querystring parameters to set/override (dict)
    :return: New URL/path
    """
    res = urlparse(url)
    query_params = dict(parse_qsl(res.query))
    for k, v in new_params.items():
        if v is None:
            query_params[str(k)] = ''
        else:
            query_params[str(k)] = str(v)
    parts = list(res)
    parts[4] = urlencode(query_params)
    return urlunparse(parts)


def url_host(url: str) -> str:
    """
    Parses hostname from URL.
    :param url: URL
    :return: hostname
    """
    res = urlparse(url)
    return res.netloc.split(':')[0] if res.netloc else ''

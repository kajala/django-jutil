from datetime import datetime
from rest_framework.exceptions import ValidationError
import pytz
from dateutil.parser import parse as dateutil_parse


TRUE_VALUES = (
    'true',
    '1',
    'yes',
)

FALSE_VALUES = (
    'none',
    'null',
    'false',
    '0',
    'no',
)


def parse_bool(v, default=None, exceptions: bool=True) -> bool:
    """
    Parses boolean value
    :param v: Input string
    :param default: Default value if exceptions=False
    :param exceptions: Raise exception on error or not
    :return: bool
    """
    if isinstance(v, bool):
        return v
    s = str(v).lower()
    if s in TRUE_VALUES:
        return True
    elif s in FALSE_VALUES:
        return False
    else:
        if exceptions:
            raise ValidationError('Failed to parse boolean from "{}"'.format(v))
        return default


def parse_datetime(v, default=None, tz=None, exceptions: bool=True) -> datetime:
    """
    Parses datetime
    :param v: Input string
    :param default: Default value if exceptions=False
    :param tz: Default pytz timezone or None if utc
    :param exceptions: Raise exception on error or not
    :return: datetime
    """
    try:
        t = dateutil_parse(v, default=datetime(2000, 1, 1))
        if tz is None:
            tz = pytz.utc
        return t if t.tzinfo else tz.localize(t)
    except Exception:
        if exceptions:
            raise ValidationError('Failed to parse datetime from "{}"'.format(v))
        return default

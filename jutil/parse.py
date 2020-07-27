import logging
from datetime import datetime
from typing import Optional, Any
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
import pytz
from dateutil.parser import parse as dateutil_parse


logger = logging.getLogger(__name__)


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


def parse_bool(v, default: Optional[bool] = None, exceptions: bool = True) -> Optional[bool]:
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
    if s in FALSE_VALUES:
        return False
    if exceptions:
        msg = _("%(value)s is not one of the available choices") % {'value': v}
        raise ValidationError(msg)
    return default


def parse_datetime(v: str, default: Optional[datetime] = None, tz: Any = None, exceptions: bool = True) -> Optional[datetime]:
    """
    Parses str to timezone-aware datetime.
    :param v: Input string to parse
    :param default: Default value to return if exceptions=False
    :param tz: Default pytz timezone or if None then use UTC as default
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
            msg = _("“%(value)s” value has an invalid format. It must be in YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ] format.") % {'value': v}
            raise ValidationError(msg)
        return default

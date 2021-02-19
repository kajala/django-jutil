import logging
from datetime import datetime, time, date
from typing import Optional, Any
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import pytz
from django.utils.dateparse import parse_datetime as django_parse_datetime
from django.utils.dateparse import parse_date as django_parse_date

logger = logging.getLogger(__name__)

TRUE_VALUES = (
    "true",
    "1",
    "yes",
)

FALSE_VALUES = (
    "none",
    "null",
    "false",
    "0",
    "no",
)


def parse_bool(v: str) -> bool:
    """
    Parses boolean value
    :param v: Input string
    :return: bool
    """
    s = str(v).lower()
    if s in TRUE_VALUES:
        return True
    if s in FALSE_VALUES:
        return False
    raise ValidationError(_("%(value)s is not one of the available choices") % {"value": v})


def parse_datetime(v: str, tz: Any = None) -> datetime:
    """
    Parses ISO date/datetime string to timezone-aware datetime.
    Supports YYYY-MM-DD date strings where time part is missing.
    Returns always timezone-aware datetime (assumes UTC if timezone missing).
    :param v: Input string to parse
    :param tz: Default pytz timezone or if None then use UTC as default
    :return: datetime with timezone
    """
    try:
        t = django_parse_datetime(v)
        if t is None:
            t_date: Optional[date] = django_parse_date(v)
            if t_date is None:
                raise ValidationError(
                    _(
                        "“%(value)s” value has an invalid format. It must be in YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ] format."
                    )
                    % {"value": v}
                )
            t = datetime.combine(t_date, time())
        if tz is None:
            tz = pytz.utc
        return t if t.tzinfo else tz.localize(t)
    except Exception:
        raise ValidationError(
            _("“%(value)s” value has an invalid format. It must be in YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ] format.")
            % {"value": v}
        )


def parse_bool_or_none(v: str) -> Optional[bool]:
    """
    Parses boolean value, or returns None if parsing fails.
    :param v: Input string
    :return: bool or None
    """
    s = str(v).lower()
    if s in TRUE_VALUES:
        return True
    if s in FALSE_VALUES:
        return False
    return None


def parse_datetime_or_none(v: str, tz: Any = None) -> Optional[datetime]:
    """
    Parses ISO date/datetime string to timezone-aware datetime.
    Supports YYYY-MM-DD date strings where time part is missing.
    Returns timezone-aware datetime (assumes UTC if timezone missing) or None if parsing fails.
    :param v: Input string to parse
    :param tz: Default pytz timezone or if None then use UTC as default
    :return: datetime with timezone or None
    """
    try:
        t = django_parse_datetime(v)
        if t is None:
            t_date: Optional[date] = django_parse_date(v)
            if t_date is None:
                return None
            t = datetime.combine(t_date, time())
        if tz is None:
            tz = pytz.utc
        return t if t.tzinfo else tz.localize(t)
    except Exception:
        return None

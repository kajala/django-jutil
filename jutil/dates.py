from datetime import datetime, timedelta
from typing import Tuple, Any, Optional
import pytz
from calendar import monthrange
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _


TIME_RANGE_CHOICES = [
    ('last_month', _('last month')),
    ('last_year', _('last year')),
    ('this_month', _('this month')),
    ('last_week', _('last week')),
    ('yesterday', _('yesterday')),
    ('today', _('today')),
    ('prev_90d', format_lazy('-90 {}', _('number.of.days'))),
    ('plus_minus_90d', format_lazy('+-90 {}', _('number.of.days'))),
    ('next_90d', format_lazy('+90 {}', _('number.of.days'))),
    ('prev_60d', format_lazy('-60 {}', _('number.of.days'))),
    ('plus_minus_60d', format_lazy('+-60 {}', _('number.of.days'))),
    ('next_60d', format_lazy('+60 {}', _('number.of.days'))),
    ('prev_30d', format_lazy('-30 {}', _('number.of.days'))),
    ('plus_minus_30d', format_lazy('+-30 {}', _('number.of.days'))),
    ('next_30d', format_lazy('+30 {}', _('number.of.days'))),
    ('prev_15d', format_lazy('-15 {}', _('number.of.days'))),
    ('plus_minus_15d', format_lazy('+-15 {}', _('number.of.days'))),
    ('next_15d', format_lazy('+15 {}', _('number.of.days'))),
    ('prev_7d', format_lazy('-7 {}', _('number.of.days'))),
    ('plus_minus_7d', format_lazy('+-7 {}', _('number.of.days'))),
    ('next_7d', format_lazy('+7 {}', _('number.of.days'))),
]

TIME_STEP_CHOICES = [
    ('daily', _('daily')),
    ('weekly', _('weekly')),
    ('monthly', _('monthly')),
]

TIME_RANGE_NAMES = list(zip(*TIME_RANGE_CHOICES))[0]

TIME_STEP_NAMES = list(zip(*TIME_STEP_CHOICES))[0]


def get_last_day_of_month(t: datetime) -> int:
    """
    Returns day number of the last day of the month
    :param t: datetime
    :return: int
    """
    tn = t + timedelta(days=32)
    tn = datetime(year=tn.year, month=tn.month, day=1)
    tt = tn - timedelta(hours=1)
    return tt.day


def localize_time_range(begin: datetime, end: datetime, tz: Any = None) -> Tuple[datetime, datetime]:
    """
    Localizes time range. Uses pytz.utc if None provided.
    :param begin: Begin datetime
    :param end: End datetime
    :param tz: pytz timezone or None (default UTC)
    :return: begin, end
    """
    if tz is None:
        tz = pytz.utc
    return tz.localize(begin), tz.localize(end)


def this_week(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """
    Returns this week begin (inclusive) and end (exclusive).
    :param today: Some date (defaults current datetime)
    :param tz: Timezone (defaults pytz UTC)
    :return: begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.utcnow()
    begin = today - timedelta(days=today.weekday())
    begin = datetime(year=begin.year, month=begin.month, day=begin.day)
    return localize_time_range(begin, begin + timedelta(days=7), tz)


def this_month(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """
    Returns current month begin (inclusive) and end (exclusive).
    :param today: Some date in the month (defaults current datetime)
    :param tz: Timezone (defaults pytz UTC)
    :return: begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.utcnow()
    begin = datetime(day=1, month=today.month, year=today.year)
    end = begin + timedelta(days=32)
    end = datetime(day=1, month=end.month, year=end.year)
    return localize_time_range(begin, end, tz)


def end_of_month(today: Optional[datetime] = None, n: int = 0, tz: Any = None) -> datetime:
    """
    Returns end-of-month (last microsecond) of given datetime (or current datetime UTC if no parameter is passed).
    :param today: Some date in the month (defaults current datetime)
    :param n: +- number of months to offset from current month. Default 0.
    :param tz: Timezone (defaults pytz UTC)
    :return: datetime
    """
    if today is None:
        today = datetime.utcnow()
    last_day = monthrange(today.year, today.month)[1]
    end = today.replace(day=last_day, hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=24)
    while n > 0:
        last_day = monthrange(end.year, end.month)[1]
        end = end.replace(day=last_day, hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=24)
        n -= 1
    while n < 0:
        end -= timedelta(days=1)
        end = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        n += 1
    end_incl = end - timedelta(microseconds=1)
    if tz is None:
        tz = pytz.utc
    return tz.localize(end_incl)


def next_week(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """
    Returns next week begin (inclusive) and end (exclusive).
    :param today: Some date (defaults current datetime)
    :param tz: Timezone (defaults pytz UTC)
    :return: begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.utcnow()
    begin = today + timedelta(days=7-today.weekday())
    begin = datetime(year=begin.year, month=begin.month, day=begin.day)
    return localize_time_range(begin, begin + timedelta(days=7), tz)


def next_month(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """
    Returns next month begin (inclusive) and end (exclusive).
    :param today: Some date in the month (defaults current datetime)
    :param tz: Timezone (defaults pytz UTC)
    :return: begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.utcnow()
    begin = datetime(day=1, month=today.month, year=today.year)
    next_mo = begin + timedelta(days=32)
    begin = datetime(day=1, month=next_mo.month, year=next_mo.year)
    following_mo = begin + timedelta(days=32)
    end = datetime(day=1, month=following_mo.month, year=following_mo.year)
    return localize_time_range(begin, end, tz)


def last_week(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """
    Returns last week begin (inclusive) and end (exclusive).
    :param today: Some date (defaults current datetime)
    :param tz: Timezone (defaults pytz UTC)
    :return: begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.utcnow()
    begin = today - timedelta(weeks=1, days=today.weekday())
    begin = datetime(year=begin.year, month=begin.month, day=begin.day)
    return localize_time_range(begin, begin + timedelta(days=7), tz)


def last_month(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """
    Returns last month begin (inclusive) and end (exclusive).
    :param today: Some date (defaults current datetime)
    :param tz: Timezone (defaults pytz UTC)
    :return: begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.utcnow()
    end = datetime(day=1, month=today.month, year=today.year)
    end_incl = end - timedelta(seconds=1)
    begin = datetime(day=1, month=end_incl.month, year=end_incl.year)
    return localize_time_range(begin, end, tz)


def last_year(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """
    Returns last year begin (inclusive) and end (exclusive).
    :param today: Some date (defaults current datetime)
    :param tz: Timezone (defaults pytz UTC)
    :return: begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.utcnow()
    end = datetime(day=1, month=1, year=today.year)
    end_incl = end - timedelta(seconds=1)
    begin = datetime(day=1, month=1, year=end_incl.year)
    return localize_time_range(begin, end, tz)


def yesterday(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """
    Returns yesterday begin (inclusive) and end (exclusive).
    :param today: Some date (defaults current datetime)
    :param tz: Timezone (defaults pytz UTC)
    :return: begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.utcnow()
    end = datetime(day=today.day, month=today.month, year=today.year)
    end_incl = end - timedelta(seconds=1)
    begin = datetime(day=end_incl.day, month=end_incl.month, year=end_incl.year)
    return localize_time_range(begin, end, tz)


def add_month(t: datetime, n: int = 1) -> datetime:
    """
    Adds +- n months to datetime.
    Clamps days to number of days in given month.
    :param t: datetime
    :param n: +- number of months to offset from current month. Default 1.
    :return: datetime
    """
    t2 = t
    for count in range(abs(n)):  # pylint: disable=unused-variable
        if n > 0:
            t2 = datetime(year=t2.year, month=t2.month, day=1) + timedelta(days=32)
        else:
            t2 = datetime(year=t2.year, month=t2.month, day=1) - timedelta(days=2)
        try:
            t2 = t.replace(year=t2.year, month=t2.month)
        except Exception:
            last_day = monthrange(t2.year, t2.month)[1]
            t2 = t.replace(year=t2.year, month=t2.month, day=last_day)
    return t2


def per_delta(start: datetime, end: datetime, delta: timedelta):
    """
    Iterates over time range in steps specified in delta.

    :param start: Start of time range (inclusive)
    :param end: End of time range (exclusive)
    :param delta: Step interval

    :return: Iterable collection of [(start+td*0, start+td*1), (start+td*1, start+td*2), ..., end)
    """
    curr = start
    while curr < end:
        curr_end = curr + delta
        yield curr, curr_end
        curr = curr_end


def per_month(start: datetime, end: datetime, n: int = 1):
    """
    Iterates over time range in one month steps.
    Clamps to number of days in given month.

    :param start: Start of time range (inclusive)
    :param end: End of time range (exclusive)
    :param n: Number of months to step. Default is 1.

    :return: Iterable collection of [(month+0, month+1), (month+1, month+2), ..., end)
    """
    curr = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while curr < end:
        curr_end = add_month(curr, n)
        yield curr, curr_end
        curr = curr_end

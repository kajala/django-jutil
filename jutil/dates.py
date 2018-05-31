from datetime import datetime, timedelta
import pytz
from calendar import monthrange


TIME_RANGE_NAMES = [
    'last_month',
    'last_year',
    'this_month',
    'last_week',
    'yesterday',
    'today',
    'prev_90d',
    'plus_minus_90d',
    'next_90d',
    'prev_60d',
    'plus_minus_60d',
    'next_60d',
    'prev_30d',
    'plus_minus_30d',
    'next_30d',
    'prev_15d',
    'plus_minus_15d',
    'next_15d',
    'prev_7d',
    'plus_minus_7d',
    'next_7d',
]

TIME_STEP_NAMES = [
    'daily',
    'weekly',
    'monthly'
]


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


def localize_time_range(begin: datetime, end: datetime, tz=None) -> (datetime, datetime):
    """
    Localizes time range. Uses pytz.utc if None provided.
    :param begin: Begin datetime
    :param end: End datetime
    :param tz: pytz timezone or None (default UTC)
    :return: begin, end
    """
    if not tz:
        tz = pytz.utc
    return tz.localize(begin), tz.localize(end)


def this_week(today: datetime=None, tz=None):
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


def this_month(today: datetime=None, tz=None):
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


def next_week(today: datetime=None, tz=None):
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


def next_month(today: datetime=None, tz=None):
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


def last_week(today: datetime=None, tz=None):
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


def last_month(today: datetime=None, tz=None):
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


def last_year(today: datetime=None, tz=None):
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


def yesterday(today: datetime=None, tz=None):
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


def add_month(t: datetime, n: int=1) -> datetime:
    """
    Adds +- n months to datetime.
    Clamps to number of days in given month.
    :param t: datetime
    :param n: count
    :return: datetime
    """
    t2 = t
    for count in range(abs(n)):
        if n > 0:
            t2 = datetime(year=t2.year, month=t2.month, day=1) + timedelta(days=32)
        else:
            t2 = datetime(year=t2.year, month=t2.month, day=1) - timedelta(days=2)
        try:
            t2 = t.replace(year=t2.year, month=t2.month)
        except Exception:
            first, last = monthrange(t2.year, t2.month)
            t2 = t.replace(year=t2.year, month=t2.month, day=last)
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


def per_month(start: datetime, end: datetime, n: int=1):
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

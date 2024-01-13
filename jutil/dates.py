import re
from datetime import datetime, timedelta, time, date, timezone
from typing import Tuple, Any, Optional, List
from calendar import monthrange
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _


TIME_RANGE_CHOICES = [
    ("yesterday", _("yesterday")),
    ("today", _("today")),
    ("tomorrow", _("tomorrow")),
    ("last_week", _("last week")),
    ("last_month", _("last month")),
    ("last_year", _("last year")),
    ("this_week", _("this week")),
    ("this_month", _("this month")),
    ("this_year", _("this year")),
    ("next_week", _("next week")),
    ("next_month", _("next month")),
    ("next_year", _("next year")),
]
# plus +- date ranges from current datetime:
# (e.g. --yesterday is full day yesterday but --prev-1d is 24h less from current time)
for d in [360, 180, 90, 60, 45, 30, 15, 7, 2, 1]:
    TIME_RANGE_CHOICES.extend(
        [
            ("prev_{}d".format(d), format_lazy("-{} {}", d, _("number.of.days"))),  # type: ignore
            ("plus_minus_{}d".format(d), format_lazy("+-{} {}", d, _("number.of.days"))),  # type: ignore
            ("next_{}d".format(d), format_lazy("+{} {}", d, _("number.of.days"))),  # type: ignore
        ]
    )

TIME_RANGE_NAMES = list(zip(*TIME_RANGE_CHOICES))[0]

TIME_STEP_DAILY = "daily"
TIME_STEP_WEEKLY = "weekly"
TIME_STEP_MONTHLY = "monthly"

TIME_STEP_TYPES = [
    TIME_STEP_DAILY,
    TIME_STEP_WEEKLY,
    TIME_STEP_MONTHLY,
]

TIME_STEP_CHOICES = [
    (TIME_STEP_DAILY, _("daily")),
    (TIME_STEP_WEEKLY, _("weekly")),
    (TIME_STEP_MONTHLY, _("monthly")),
]

TIME_STEP_NAMES = list(zip(*TIME_STEP_CHOICES))[0]


def utc_date_to_datetime(date_val: date) -> datetime:
    return datetime.combine(date_val, time(0, 0)).replace(tzinfo=timezone.utc)


def replace_range_tzinfo(begin: datetime, end: datetime, tzinfo: Any = None) -> Tuple[datetime, datetime]:
    """
    Replaces time range tzinfo. Uses timezone.utc if None provided.
    :param begin: Begin datetime
    :param end: End datetime
    :param tzinfo: ZoneInfo or None (default timezone.utc)
    :return: begin, end
    """
    if tzinfo is None:
        tzinfo = timezone.utc
    return begin.replace(tzinfo=tzinfo), end.replace(tzinfo=tzinfo)


def get_last_day_of_month(today: Optional[datetime] = None) -> int:
    """Returns day number of the last day of the month

    Args:
        today: Default UTC now

    Returns:
        int
    """
    if today is None:
        today = datetime.now()
    return monthrange(today.year, today.month)[1]


def end_of_month(today: Optional[datetime] = None, n: int = 0, tz: Any = None) -> datetime:
    """Returns end-of-month (last microsecond) of given datetime (or current datetime UTC if no parameter is passed).

    Args:
        today: Some date in the month (defaults current datetime)
        n: +- number of months to offset from current month. Default 0.
        tz: Timezone (defaults timezone.utc)

    Returns:
        datetime
    """
    if today is None:
        today = datetime.now()
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
        tz = timezone.utc
    return end_incl.replace(tzinfo=tz)


def this_week(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """Returns this week begin (inclusive) and end (exclusive).
    Week is assumed to start from Monday (ISO).

    Args:
        today: Some date (defaults current datetime)
        tz: Timezone (defaults timezone.utc)

    Returns:
        begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.now()
    begin = today - timedelta(days=today.weekday())
    begin = datetime(year=begin.year, month=begin.month, day=begin.day)
    return replace_range_tzinfo(begin, begin + timedelta(days=7), tz)


def this_month(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """Returns current month begin (inclusive) and end (exclusive).

    Args:
        today: Some date in the month (defaults current datetime)
        tz: Timezone (defaults timezone.utc)

    Returns:
        begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.now()
    begin = datetime(day=1, month=today.month, year=today.year)
    end = begin + timedelta(days=32)
    end = datetime(day=1, month=end.month, year=end.year)
    return replace_range_tzinfo(begin, end, tz)


def this_year(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """Returns this year begin (inclusive) and end (exclusive).

    Args:
        today: Some date (defaults current datetime)
        tz: Timezone (defaults timezone.utc)

    Returns:
        begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.now()
    begin = datetime(day=1, month=1, year=today.year)
    end = datetime(day=1, month=1, year=begin.year + 1)
    return replace_range_tzinfo(begin, end, tz)


def next_year(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    if today is None:
        today = datetime.now()
    begin = datetime(day=1, month=1, year=today.year + 1)
    end = datetime(day=1, month=1, year=begin.year + 2)
    return replace_range_tzinfo(begin, end, tz)


def next_week(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """Returns next week begin (inclusive) and end (exclusive).

    Args:
        today: Some date (defaults current datetime)
        tz: Timezone (defaults timezone.utc)

    Returns:
        begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.now()
    begin = today + timedelta(days=7 - today.weekday())
    begin = datetime(year=begin.year, month=begin.month, day=begin.day)
    return replace_range_tzinfo(begin, begin + timedelta(days=7), tz)


def next_month(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """Returns next month begin (inclusive) and end (exclusive).

    Args:
        today: Some date in the month (defaults current datetime)
        tz: Timezone (defaults timezone.utc)

    Returns:
        begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.now()
    begin = datetime(day=1, month=today.month, year=today.year)
    next_mo = begin + timedelta(days=32)
    begin = datetime(day=1, month=next_mo.month, year=next_mo.year)
    following_mo = begin + timedelta(days=32)
    end = datetime(day=1, month=following_mo.month, year=following_mo.year)
    return replace_range_tzinfo(begin, end, tz)


def last_week(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """Returns last week begin (inclusive) and end (exclusive).

    Args:
        today: Some date (defaults current datetime)
        tz: Timezone (defaults timezone.utc)

    Returns:
        begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.now()
    begin = today - timedelta(weeks=1, days=today.weekday())
    begin = datetime(year=begin.year, month=begin.month, day=begin.day)
    return replace_range_tzinfo(begin, begin + timedelta(days=7), tz)


def last_month(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """Returns last month begin (inclusive) and end (exclusive).

    Args:
        today: Some date (defaults current datetime)
        tz: Timezone (defaults timezone.utc)

    Returns:
        begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.now()
    end = datetime(day=1, month=today.month, year=today.year)
    end_incl = end - timedelta(seconds=1)
    begin = datetime(day=1, month=end_incl.month, year=end_incl.year)
    return replace_range_tzinfo(begin, end, tz)


def last_year(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """Returns last year begin (inclusive) and end (exclusive).

    Args:
        today: Some date (defaults current datetime)
        tz: Timezone (defaults timezone.utc)

    Returns:
        begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.now()
    end = datetime(day=1, month=1, year=today.year)
    end_incl = end - timedelta(seconds=1)
    begin = datetime(day=1, month=1, year=end_incl.year)
    return replace_range_tzinfo(begin, end, tz)


def yesterday(today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """Returns yesterday begin (inclusive) and end (exclusive).

    Args:
        today: Some date (defaults current datetime)
        tz: Timezone (defaults timezone.utc)

    Returns:
        begin (inclusive), end (exclusive)
    """
    if today is None:
        today = datetime.now()
    end = datetime(day=today.day, month=today.month, year=today.year)
    end_incl = end - timedelta(seconds=1)
    begin = datetime(day=end_incl.day, month=end_incl.month, year=end_incl.year)
    return replace_range_tzinfo(begin, end, tz)


def add_month(t: datetime, n: int = 1) -> datetime:
    """Adds +- n months to datetime.
    Clamps days to number of days in given month.

    Args:
        t: datetime
        n: +- number of months to offset from current month. Default 1.

    Returns:
        datetime
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
    """Iterates over time range in steps specified in delta.

    Args:
        start: Start of time range (inclusive)
        end: End of time range (exclusive)
        delta: Step interval

    Returns:
        Iterable collection of [(start+td*0, start+td*1), (start+td*1, start+td*2), ..., end)
    """
    curr = start
    while curr < end:
        curr_end = curr + delta
        yield curr, curr_end
        curr = curr_end


def per_month(start: datetime, end: datetime, n: int = 1):
    """Iterates over time range in one month steps.
    Clamps to number of days in given month.

    Args:
        start: Start of time range (inclusive)
        end: End of time range (exclusive)
        n: Number of months to step. Default is 1.

    Returns:
        Iterable collection of [(month+0, month+1), (month+1, month+2), ..., end)
    """
    curr = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while curr < end:
        curr_end = add_month(curr, n)
        yield curr, curr_end
        curr = curr_end


def get_time_steps(step_type: str, begin: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
    """Returns time stamps by time step type [TIME_STEP_DAILY, TIME_STEP_WEEKLY, TIME_STEP_MONTHLY].
    For example daily steps for a week returns 7 [begin, end) ranges for each day of the week.

    Args:
        step_type: One of TIME_STEP_DAILY, TIME_STEP_WEEKLY, TIME_STEP_MONTHLY
        begin: datetime
        end: datetime

    Returns:
        List of [begin, end), one for reach time step unit
    """
    after_end = end
    if TIME_STEP_DAILY == step_type:
        after_end += timedelta(days=1)
    elif TIME_STEP_WEEKLY == step_type:
        after_end += timedelta(days=7)
    elif TIME_STEP_MONTHLY == step_type:
        after_end = add_month(end)
    else:
        raise ValueError('Time step "{}" not one of {}'.format(step_type, TIME_STEP_TYPES))

    begins: List[datetime] = []
    t0 = t = begin
    n = 1
    while t < after_end:
        begins.append(t)
        if step_type == TIME_STEP_DAILY:
            t = t0 + timedelta(days=n)
        elif step_type == TIME_STEP_WEEKLY:
            t = t0 + timedelta(days=7 * n)
        elif step_type == TIME_STEP_MONTHLY:
            t = add_month(t0, n)
        n += 1
    return [(begins[i], begins[i + 1]) for i in range(len(begins) - 1)]


def get_date_range_by_name(name: str, today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:  # noqa
    """Returns a timezone-aware date range by symbolic name.

    Args:
        name: Name of the date range. See TIME_RANGE_CHOICES.
        today: Optional current datetime. Default is datetime.now().
        tz: Optional timezone. Default is UTC.

    Returns:
        datetime (begin, end)
    """
    if today is None:
        today = datetime.now()
    begin = today.replace(hour=0, minute=0, second=0, microsecond=0)

    if name == "last_week":
        return last_week(today, tz)
    if name == "last_month":
        return last_month(today, tz)
    if name == "last_year":
        return last_year(today, tz)
    if name == "this_week":
        return this_week(today, tz)
    if name == "this_month":
        return this_month(today, tz)
    if name == "this_year":
        return this_year(today, tz)
    if name == "next_week":
        return next_week(today, tz)
    if name == "next_month":
        return next_month(today, tz)
    if name == "next_year":
        return next_year(today, tz)
    if name == "yesterday":
        return yesterday(today, tz)
    if name == "today":
        return replace_range_tzinfo(begin, begin + timedelta(hours=24), tz)
    if name == "tomorrow":
        return replace_range_tzinfo(begin + timedelta(hours=24), begin + timedelta(hours=48), tz)

    m = re.match(r"^plus_minus_(\d+)d$", name)
    if m:
        days = int(m.group(1))
        return replace_range_tzinfo(begin - timedelta(days=days), today + timedelta(days=days), tz)

    m = re.match(r"^prev_(\d+)d$", name)
    if m:
        days = int(m.group(1))
        return replace_range_tzinfo(begin - timedelta(days=days), today, tz)

    m = re.match(r"^next_(\d+)d$", name)
    if m:
        days = int(m.group(1))
        return replace_range_tzinfo(begin, today + timedelta(days=days), tz)

    raise ValueError("Invalid date range name: {}".format(name))

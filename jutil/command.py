import logging
import re
import traceback
from datetime import datetime, timedelta
from typing import Tuple, List, Any, Optional
from django.core.management.base import BaseCommand, CommandParser
from django.utils.timezone import now
from django.conf import settings
from jutil.dates import (
    last_month,
    yesterday,
    TIME_RANGE_NAMES,
    TIME_STEP_NAMES,
    this_month,
    last_year,
    last_week,
    localize_time_range,
    this_year,
    this_week,
    get_time_steps,
)
from jutil.email import send_email
import getpass
from django.utils import translation
from jutil.parse import parse_datetime


logger = logging.getLogger(__name__)


class SafeCommand(BaseCommand):
    """
    BaseCommand which catches, logs and emails errors.
    Uses list of emails from settings.ADMINS.
    Implement do() in derived classes.
    """

    def handle(self, *args, **kwargs):
        try:
            if hasattr(settings, "LANGUAGE_CODE"):
                translation.activate(settings.LANGUAGE_CODE)
            return self.do(*args, **kwargs)
        except Exception as e:
            msg = "ERROR: {}\nargs: {}\nkwargs: {}\n{}".format(str(e), args, kwargs, traceback.format_exc())
            logger.error(msg)
            if not settings.DEBUG:
                send_email(settings.ADMINS, "Error @ {}".format(getpass.getuser()), msg)
            raise

    def do(self, *args, **kwargs):
        pass


def add_date_range_arguments(parser: CommandParser):
    """
    Adds following arguments to the CommandParser:

    Ranges:
      --begin BEGIN
      --end END
      --last-year
      --last-month
      --last-week
      --this-year
      --this-month
      --this-week
      --yesterday
      --today
      --prev-90d
      --plus-minus-90d
      --next-90d
      --prev-60d
      --plus-minus-60d
      --next-60d
      --prev-30d
      --plus-minus-30d
      --next-30d
      --prev-15d
      --plus-minus-15d
      --next-15d
      --prev-7d
      --plus-minus-7d
      --next-7d
      --prev-2d
      --plus-minus-2d
      --next-2d
      --prev-1d
      --plus-minus-1d
      --next-1d

    Steps:
      --daily
      --weekly
      --monthly

    :param parser:
    :return:
    """
    parser.add_argument("--begin", type=str)
    parser.add_argument("--end", type=str)
    for v in TIME_STEP_NAMES:
        parser.add_argument("--" + v.replace("_", "-"), action="store_true")
    for v in TIME_RANGE_NAMES:
        parser.add_argument("--" + v.replace("_", "-"), action="store_true")


def get_date_range_by_name(name: str, today: Optional[datetime] = None, tz: Any = None) -> Tuple[datetime, datetime]:
    """
    Returns a timezone-aware date range by symbolic name.
    :param name: Name of the date range. See add_date_range_arguments().
    :param today: Optional current datetime. Default is now().
    :param tz: Optional timezone. Default is UTC.
    :return: datetime (begin, end)
    """
    if today is None:
        today = datetime.utcnow()
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
    if name == "yesterday":
        return yesterday(today, tz)
    if name == "today":
        begin = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end = begin + timedelta(hours=24)
        return localize_time_range(begin, end, tz)
    m = re.match(r"^plus_minus_(\d+)d$", name)
    if m:
        days = int(m.group(1))
        return localize_time_range(today - timedelta(days=days), today + timedelta(days=days), tz)
    m = re.match(r"^prev_(\d+)d$", name)
    if m:
        days = int(m.group(1))
        return localize_time_range(today - timedelta(days=days), today, tz)
    m = re.match(r"^next_(\d+)d$", name)
    if m:
        days = int(m.group(1))
        return localize_time_range(today, today + timedelta(days=days), tz)
    raise ValueError("Invalid date range name: {}".format(name))


def parse_date_range_arguments(
    options: dict, default_range: str = "last_month"
) -> Tuple[datetime, datetime, List[Tuple[datetime, datetime]]]:
    """
    Parses date range from input and returns timezone-aware date range and
    interval list according to 'step' name argument (optional).
    See add_date_range_arguments()
    :param options: Parsed arguments passed to the command
    :param default_range: Default datetime range to return if no other selected
    :return: begin, end, [(begin1,end1), (begin2,end2), ...]
    """
    begin, end = get_date_range_by_name(default_range)
    for range_name in TIME_RANGE_NAMES:
        if options.get(range_name):
            begin, end = get_date_range_by_name(range_name)
    if options.get("begin"):
        begin = parse_datetime(options["begin"])  # type: ignore
        end = now()
    if options.get("end"):
        end = parse_datetime(options["end"])  # type: ignore

    step_type = ""
    for step_name in TIME_STEP_NAMES:
        if options.get(step_name):
            if step_type:
                raise ValueError("Cannot use --{} and --{} simultaneously".format(step_type, step_name))
            step_type = step_name
    if step_type:
        steps = get_time_steps(step_type, begin, end)
    else:
        steps = [(begin, end)]
    return begin, end, steps

import logging
import re
import traceback
from datetime import datetime, timedelta
import pytz
from dateutil import rrule
from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandParser
from django.utils.timezone import now
from django.conf import settings
from jutil.dates import last_month, yesterday, TIME_RANGE_NAMES, TIME_STEP_NAMES, this_month, last_year, last_week, \
    localize_time_range
from jutil.email import send_email
import getpass
from django.utils import translation


logger = logging.getLogger(__name__)


class SafeCommand(BaseCommand):
    """
    BaseCommand which catches, logs and emails errors.
    Uses list of emails from settings.ADMINS.
    Implement do() in derived classes.
    """

    def handle(self, *args, **options):
        try:
            if hasattr(settings, 'LANGUAGE_CODE'):
                translation.activate(settings.LANGUAGE_CODE)
            return self.do(*args, **options)
        except Exception as e:
            msg = "ERROR: {} {}".format(str(e), traceback.format_exc())
            logger.error(msg)
            print(msg)
            if not settings.DEBUG:
                send_email(settings.ADMINS, 'Error @ {}'.format(getpass.getuser()), msg)


def add_date_range_arguments(parser: CommandParser):
    parser.add_argument('--begin', type=str)
    parser.add_argument('--end', type=str)
    for v in TIME_STEP_NAMES:
        parser.add_argument('--' + v.replace('_', '-'), action='store_true')
    for v in TIME_RANGE_NAMES:
        parser.add_argument('--' + v.replace('_', '-'), action='store_true')


def get_date_range_by_name(name: str, today: datetime=None, tz=None) -> (datetime, datetime):
    """
    :param name: yesterday, last_month
    :param today: Optional current datetime. Default is now().
    :param tz: Optional timezone. Default is UTC.
    :return: datetime (begin, end)
    """
    if today is None:
        today = datetime.utcnow()
    if name == 'last_month':
        return last_month(today, tz)
    elif name == 'last_week':
        return last_week(today, tz)
    elif name == 'this_month':
        return this_month(today, tz)
    elif name == 'last_year':
        return last_year(today, tz)
    elif name == 'yesterday':
        return yesterday(today, tz)
    elif name == 'today':
        begin = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end = begin + timedelta(hours=24)
        return localize_time_range(begin, end, tz)
    else:
        m = re.match(r'^plus_minus_(\d+)d$', name)
        if m:
            days = int(m.group(1))
            return localize_time_range(today - timedelta(days=days), today + timedelta(days=days), tz)
        m = re.match(r'^prev_(\d+)d$', name)
        if m:
            days = int(m.group(1))
            return localize_time_range(today - timedelta(days=days), today, tz)
        m = re.match(r'^next_(\d+)d$', name)
        if m:
            days = int(m.group(1))
            return localize_time_range(today, today + timedelta(days=days), tz)
    raise ValueError('Invalid date range name: {}'.format(name))


def parse_date_range_arguments(options: dict, default_range='last_month') -> (datetime, datetime, list):
    """
    :param options:
    :param default_range: Default datetime range to return if no other selected
    :return: begin, end, [(begin1,end1), (begin2,end2), ...]
    """
    begin, end = get_date_range_by_name(default_range)
    for range_name in TIME_RANGE_NAMES:
        if options.get(range_name):
            begin, end = get_date_range_by_name(range_name)
    if options.get('begin'):
        t = parse(options['begin'], default=datetime(2000, 1, 1))
        begin = pytz.utc.localize(t)
        end = now()
    if options.get('end'):
        end = pytz.utc.localize(parse(options['end'], default=datetime(2000, 1, 1)))

    step_type = None
    after_end = end
    for step_name in TIME_STEP_NAMES:
        if options.get(step_name):
            step_type = getattr(rrule, step_name.upper())
            if rrule.DAILY == step_type:
                after_end += timedelta(days=1)
            if rrule.WEEKLY == step_type:
                after_end += timedelta(days=7)
            if rrule.MONTHLY == step_type:
                after_end += timedelta(days=31)
    steps = None
    if step_type:
        begins = [t for t in rrule.rrule(step_type, dtstart=begin, until=after_end)]
        steps = [(begins[i], begins[i+1]) for i in range(len(begins)-1)]
    if steps is None:
        steps = [(begin, end)]
    return begin, end, steps

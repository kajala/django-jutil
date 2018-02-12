import logging
import traceback
from datetime import datetime, timedelta
import pytz
from dateutil import rrule
from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandParser
from django.utils.timezone import now
from django.conf import settings
from jutil.dates import last_month, yesterday, TIME_RANGE_NAMES, TIME_STEP_NAMES, this_month, last_year, last_week
from jutil.email import send_email
import getpass
from django.utils import translation


logger = logging.getLogger(__name__)


class SafeCommand(BaseCommand):
    """
    BaseCommand which catches, logs and emails errors.
    Uses list of emails from settings.ADMINS.
    """

    def handle(self, *args, **options):
        try:
            if hasattr(settings, 'LANGUAGE_CODE'):
                translation.activate(settings.LANGUAGE_CODE)
            self.do(*args, **options)
        except Exception as e:
            msg = "ERROR: {} {}".format(str(e), traceback.format_exc())
            logger.error(msg)
            print(msg)
            if not settings.DEBUG:
                send_email(settings.ADMINS, 'Error @ {}'.format(getpass.getuser()), msg)


def add_date_range_arguments(parser: CommandParser):
    parser.add_argument('--begin', type=str)
    parser.add_argument('--end', type=str)
    for step in TIME_STEP_NAMES:
        parser.add_argument('--' + step.replace('_', '-'), action='store_true')
    for step in TIME_RANGE_NAMES:
        parser.add_argument('--' + step.replace('_', '-'), action='store_true')


def get_date_range_by_name(name: str) -> (datetime, datetime):
    """
    :param name: yesterday, last_month
    :return: datetime (begin, end)
    """
    if name == 'last_month':
        return last_month()
    elif name == 'last_week':
        return last_week()
    elif name == 'this_month':
        return this_month()
    elif name == 'last_year':
        return last_year()
    elif name == 'yesterday':
        return yesterday()
    elif name == 'from2000':
        return pytz.utc.localize(datetime(2000, 1, 1)), now()
    elif name == 'plus_minus_30d':
        return now() - timedelta(days=30), now() + timedelta(days=30)
    elif name == 'next_30d':
        return now(), now() + timedelta(days=30)
    elif name == 'plus_minus_60d':
        return now() - timedelta(days=60), now() + timedelta(days=60)
    elif name == 'next_60d':
        return now(), now() + timedelta(days=60)
    elif name == 'plus_minus_90d':
        return now() - timedelta(days=90), now() + timedelta(days=90)
    elif name == 'next_90d':
        return now(), now() + timedelta(days=90)
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

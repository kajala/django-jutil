import logging
import traceback
from datetime import datetime
from typing import Tuple, List, Any
from django.core.management import get_commands, load_command_class
from django.core.management.base import BaseCommand, CommandParser
from django.utils.timezone import now
from django.conf import settings
from jutil.dates import (
    TIME_RANGE_NAMES,
    TIME_STEP_NAMES,
    get_time_steps,
    get_date_range_by_name,
)
from jutil.email import send_email
import getpass
from django.utils import translation
from jutil.parse import parse_datetime


logger = logging.getLogger(__name__)


class SafeCommand(BaseCommand):
    """
    BaseCommand which activates LANGUAGE_CODE locale, catches, logs and emails errors.
    Uses list of emails from settings.ADMINS.
    Implement do() in derived classes with identical args as normal handle().
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

    @property
    def name(self) -> str:
        """
        Returns name of the CLI management command.
        For example, customers/management/commands/list_customers.py Command would return "list_customers".
        Returns:
            str
        """
        return self.__class__.__module__.rsplit(".", 1)[1]


def add_date_range_arguments(parser: CommandParser):
    """Adds following arguments to the CommandParser:

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

    Args:
        parser

    Returns:

    """
    parser.add_argument("--begin", type=str)
    parser.add_argument("--end", type=str)
    for v in TIME_STEP_NAMES:
        parser.add_argument("--" + v.replace("_", "-"), action="store_true")
    for v in TIME_RANGE_NAMES:
        parser.add_argument("--" + v.replace("_", "-"), action="store_true")


def parse_date_range_arguments(options: dict, default_range: str = "last_month", tz: Any = None) -> Tuple[datetime, datetime, List[Tuple[datetime, datetime]]]:
    """Parses date range from input and returns timezone-aware date range and
    interval list according to 'step' name argument (optional).
    See add_date_range_arguments()

    Args:
        options: Parsed arguments passed to the command
        default_range: Default datetime range to return if no other selected
        tz: Optional timezone to use. Default is UTC.

    Returns:
        begin, end, [(begin1,end1), (begin2,end2), ...]
    """
    begin, end = get_date_range_by_name(default_range, tz=tz)
    for range_name in TIME_RANGE_NAMES:
        if options.get(range_name):
            begin, end = get_date_range_by_name(range_name, tz=tz)
    if options.get("begin"):
        begin = parse_datetime(options["begin"], tz)  # type: ignore
        end = now()
    if options.get("end"):
        end = parse_datetime(options["end"], tz)  # type: ignore

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


def get_command_by_name(command_name: str) -> BaseCommand:
    """Gets Django management BaseCommand derived command class instance by name."""
    all_commands = get_commands()
    app_name = all_commands.get(command_name)
    if app_name is None:
        raise Exception(f"Django management command {command_name} not found")  # noqa
    command = app_name if isinstance(app_name, BaseCommand) else load_command_class(app_name, command_name)
    assert isinstance(command, BaseCommand)
    return command


def get_command_name(command: BaseCommand) -> str:
    """Gets Django management BaseCommand name from instance."""
    module_name = command.__class__.__module__
    res = module_name.rsplit(".", 1)
    if len(res) != 2:
        raise Exception(f"Failed to parse Django command name from {module_name}")  # noqa
    return res[1]

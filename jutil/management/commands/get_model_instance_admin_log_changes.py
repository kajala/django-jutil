from django.core.management.base import CommandParser
from django.utils.timezone import now
from jutil.admin import get_model_instance_admin_log_changes
from jutil.command import SafeCommand
from django.apps import apps
import logging
from jutil.parse import parse_datetime

logger = logging.getLogger(__name__)  # type: ignore


class Command(SafeCommand):
    help = "Lists object field changes based on extended admin log entries"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("app_and_model", type=str, help="For example 'myapp.MyModel'")
        parser.add_argument("pk", type=str, help="Object primary key")
        parser.add_argument("--field", type=str, help="If you are interested only in specific field")
        parser.add_argument("--timestamp", type=str, help="Report values at specific timestamp")
        parser.add_argument("--max-entries", type=int, help="Maximum number of log entries to report. Default is all.")
        parser.add_argument("--ordering", type=str, help="Ordering of the entries, default is newest first ('-pk').", default="-pk")
        parser.add_argument("--verbose", action="store_true", help="Verbose output")

    def do(self, *args, **kwargs):
        app_and_model = kwargs["app_and_model"]
        if app_and_model.count(".") != 1:
            print(f"ERROR: app_and_model must follow 'myapp.MyModel' format, '{app_and_model}' given")
            return
        app_name, model_name = app_and_model.split(".")
        timestamp = parse_datetime(kwargs["timestamp"]) if kwargs["timestamp"] else now()
        field_name = kwargs["field"] if kwargs["field"] else ""
        verbose = kwargs["verbose"]
        ordering = kwargs["ordering"]
        max_entries = kwargs["max_entries"]
        cls = apps.get_model(app_name, model_name)
        pk = kwargs["pk"]
        obj = cls.objects.filter(pk=pk).first()  # type: ignore
        if obj is None:
            print(f"ERROR: object pk={pk} not found")
            return

        for item in get_model_instance_admin_log_changes(
            obj, field_name=field_name, timestamp=timestamp, ordering=ordering, verbose=verbose, max_entries=max_entries
        ):
            print(f"{item} [{item.log_entry.user}]")

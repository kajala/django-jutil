import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import CommandParser
from jutil.command import SafeCommand


class Command(SafeCommand):
    help = "Lists project's top-level apps directly under BASE_DIR"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--nl", action="store_true", help="Use \\n as app separator")

    def do(self, *args, **kw):
        sep = " "
        if kw["nl"]:
            sep = "\n"
        for app in apps.get_app_configs():
            name = app.name
            full_path = os.path.join(os.path.join(settings.BASE_DIR, name), "apps.py")
            if os.path.isfile(full_path):
                self.stdout.write(name, ending=sep)

import json
from django.core.management.base import CommandParser
from jutil.command import SafeCommand
from jutil.request import get_geo_ip


class Command(SafeCommand):
    help = "Gets info about IP address"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("ip", type=str)

    def do(self, *args, **kw):
        data = get_geo_ip(kw["ip"])
        self.stdout.write(json.dumps(data, indent=4))

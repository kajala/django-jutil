import json
from django.core.management.base import CommandParser
from jutil.command import SafeCommand
from jutil.request import get_geo_ip


class Command(SafeCommand):
    help = "Gets info about IP address"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("ip", type=str)
        parser.add_argument("--verbose", action="store_true")

    def do(self, *args, **kw):
        geo_ip = get_geo_ip(kw["ip"], verbose=kw["verbose"])
        self.stdout.write(json.dumps(geo_ip.__dict__, indent=4))

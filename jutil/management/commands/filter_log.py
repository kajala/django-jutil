from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = (
        "Simple Django log filter. "
        "Finds match and then show the line contents following the matched string."
        "Use grep for more complex regular expression matching."
    )

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("content", type=str)
        parser.add_argument("--file", type=str)

    def handle(self, *args, **kwargs):
        content = kwargs["content"]
        file = kwargs["file"] or settings.LOGGING.get("handlers", {}).get("file", {}).get("filename", "")
        if not file:
            raise Exception("Specify --file or make sure settings.LOGGING['handlers']['file']['filename'] is set")

        content_len = len(content)
        with open(file, "rt") as fp:
            line = fp.readline()
            while line:
                i = line.find(content)
                if i >= 0:
                    rest = line[i + content_len :].lstrip()
                    self.stdout.write(rest)
                line = fp.readline()

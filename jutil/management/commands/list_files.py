import json

from django.core.management.base import CommandParser
from jutil.command import SafeCommand
from jutil.files import list_files


class Command(SafeCommand):
    help = "Wrapper for testing list_files helper function output"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("dir_name", type=str)
        parser.add_argument("--suffix", type=str)
        parser.add_argument("--ignore-case", action="store_true")
        parser.add_argument("--recurse", action="store_true")
        parser.add_argument("--json", action="store_true")
        parser.add_argument("--use-media-root", action="store_true")

    def do(self, *args, **kw):
        dir_name = kw["dir_name"]
        suffix = kw["suffix"] or ""
        recurse = kw["recurse"]
        ignore_case = kw["ignore_case"]
        use_media_root = kw["use_media_root"]
        out = list_files(dir_name, suffix=suffix, ignore_case=ignore_case, use_media_root=use_media_root, recurse=recurse)
        if kw["json"]:
            json_str = json.dumps(out, indent=4)
            self.stdout.writelines([json_str])
        else:
            self.stdout.writelines(out)

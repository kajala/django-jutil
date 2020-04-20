# (generated with --quick)

from typing import Any

BaseCommand: Any
CommandParser: Any
Q: Any
User: Any

class Command(Any):
    help: str
    def add_arguments(self, parser) -> None: ...
    def handle(self, *args, **options) -> None: ...

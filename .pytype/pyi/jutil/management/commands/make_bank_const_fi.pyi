# (generated with --quick)

import collections
import jutil.command
from typing import Any, Type

CommandParser: Any
FI_BANK_NAME_BY_BIC: dict
FI_BIC_BY_ACCOUNT_NUMBER: dict
SafeCommand: Type[jutil.command.SafeCommand]
ValidationError: Any

class Command(jutil.command.SafeCommand):
    help: str
    def add_arguments(self, parser) -> None: ...
    def do(self, *args, **kw) -> None: ...

def fi_iban_load_map(filename: str) -> dict: ...
def sorted_dict(d: dict) -> collections.OrderedDict: ...

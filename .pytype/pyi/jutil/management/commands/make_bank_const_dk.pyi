# (generated with --quick)

import jutil.command
from typing import Any, Dict, Type, TypeVar

CommandParser: Any
DK_BANK_CLEARING_MAP: Dict[str, str]
SafeCommand: Type[jutil.command.SafeCommand]
csv: module

_T = TypeVar('_T')

class Command(jutil.command.SafeCommand):
    help: str
    def add_arguments(self, parser) -> None: ...
    def do(self, *args, **kw) -> None: ...

def copy(x: _T) -> _T: ...
def dk_iban_load_map(filename: str) -> list: ...
def is_int(x) -> bool: ...

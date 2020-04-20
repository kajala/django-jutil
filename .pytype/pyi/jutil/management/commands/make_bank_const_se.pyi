# (generated with --quick)

import jutil.command
from typing import Any, Tuple, Type, TypeVar

CommandParser: Any
SE_BANK_CLEARING_LIST: Tuple[Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int], Tuple[str, str, str, int]]
SafeCommand: Type[jutil.command.SafeCommand]
csv: module
re: module

_T = TypeVar('_T')

class Command(jutil.command.SafeCommand):
    help: str
    def add_arguments(self, parser) -> None: ...
    def do(self, *args, **kw) -> None: ...

def copy(x: _T) -> _T: ...
def se_iban_load_map(filename: str) -> list: ...

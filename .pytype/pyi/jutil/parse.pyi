# (generated with --quick)

import dateutil.parser
from typing import Any, IO, Optional, Tuple, Type, Union

FALSE_VALUES: Tuple[str, str, str, str, str]
TRUE_VALUES: Tuple[str, str, str]
ValidationError: Any
_: Any
datetime: Type[datetime.datetime]
pytz: module

def dateutil_parse(timestr: Union[bytes, str, IO], parserinfo: Optional[dateutil.parser.parserinfo] = ..., **kwargs) -> datetime.datetime: ...
def parse_bool(v, default = ..., exceptions: bool = ...) -> bool: ...
def parse_datetime(v: str, default = ..., tz = ..., exceptions: bool = ...) -> datetime.datetime: ...

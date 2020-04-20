# (generated with --quick)

from typing import Any, Tuple

logger: logging.Logger
logging: module
requests: module
settings: Any
socket: module

def get_geo_ip(ip: str, exceptions: bool = ..., timeout: int = ...) -> dict: ...
def get_ip_info(ip: str, exceptions: bool = ..., timeout: int = ...) -> Tuple[str, str, str]: ...

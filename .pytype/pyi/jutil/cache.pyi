# (generated with --quick)

from typing import List

logger: logging.Logger
logging: module

class CachedFieldsMixin:
    __doc__: str
    cached_fields: List[nothing]
    def update_cached_fields(self, commit: bool = ..., exceptions: bool = ..., updated_fields: list = ...) -> None: ...
    def update_cached_fields_pre_save(self, update_fields: list) -> None: ...

def update_cached_fields(*args) -> None: ...

# (generated with --quick)

from typing import Any

permissions: module

class IsSameUser(Any):
    __doc__: str
    def has_object_permission(self, request, view, obj) -> Any: ...

class UserIsOwner(Any):
    __doc__: str
    user_field: str
    def has_object_permission(self, request, view, obj) -> Any: ...

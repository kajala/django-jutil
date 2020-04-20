# (generated with --quick)

from typing import Any

NotAuthenticated: Any
Request: Any
User: Any

class AuthUserMixin:
    auth_user: Any

def require_auth(request, exceptions: bool = ...) -> Any: ...

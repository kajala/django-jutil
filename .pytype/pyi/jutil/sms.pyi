# (generated with --quick)

import requests.models
from typing import Any

requests: module
settings: Any

def phone_filter(v: str) -> str: ...
def send_sms(phone: str, message: str, sender: str = ..., **kw) -> requests.models.Response: ...

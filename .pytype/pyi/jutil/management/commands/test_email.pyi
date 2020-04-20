# (generated with --quick)

import jutil.command
from typing import Any, Type

CommandParser: Any
SafeCommand: Type[jutil.command.SafeCommand]
now: Any
os: module
settings: Any

class Command(jutil.command.SafeCommand):
    help: str
    def add_arguments(self, parser) -> None: ...
    def do(self, *args, **kw) -> None: ...

def send_email(recipients: list, subject: str, text: str = ..., html: str = ..., sender: str = ..., files: list = ..., cc_recipients: list = ..., bcc_recipients: list = ..., exceptions: bool = ...) -> Any: ...
def send_email_sendgrid(recipients: list, subject: str, text: str = ..., html: str = ..., sender: str = ..., files: list = ..., cc_recipients: list = ..., bcc_recipients: list = ..., exceptions: bool = ...) -> Any: ...
def send_email_smtp(recipients: list, subject: str, text: str = ..., html: str = ..., sender: str = ..., files: list = ..., cc_recipients: list = ..., bcc_recipients: list = ..., exceptions: bool = ...) -> int: ...

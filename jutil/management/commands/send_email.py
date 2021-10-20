import os
from django.conf import settings
from django.core.management.base import CommandParser
from django.utils.html import strip_tags
from django.utils.timezone import now
from jutil.command import SafeCommand
from jutil.email import send_email, send_email_smtp, send_email_sendgrid


class Command(SafeCommand):
    help = "Sends email with (optional) attachment"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("to", type=str)
        parser.add_argument("--cc", type=str)
        parser.add_argument("--bcc", type=str)
        parser.add_argument("--sender", type=str)
        parser.add_argument("--subject", type=str)
        parser.add_argument("--body", type=str)
        parser.add_argument("--body-file", type=str)
        parser.add_argument("--attach", type=str, nargs="*")
        parser.add_argument("--smtp", action="store_true")
        parser.add_argument("--sendgrid", action="store_true")

    def do(self, *args, **kw):  # pylint: disable=too-many-branches
        files = kw["attach"] if kw["attach"] else []
        if not files:
            full_path = os.path.join(settings.BASE_DIR, "data/attachment.jpg")
            if os.path.isfile(full_path):
                files.append(full_path)
        subject = "hello " + now().isoformat()
        html = '<h1>html text</h1><p><a href="https://kajala.com/">Kajala Group Ltd.</a></p>'
        if kw["body"]:
            html = kw["body"]
        if kw["body_file"]:
            html = open(kw["body_file"], "rt", encoding="utf-8").read()  # pylint: disable=consider-using-with
        if kw["subject"]:
            subject = kw["subject"]
        text = strip_tags(html)
        sender = kw["sender"] if kw["sender"] else ""

        if kw["smtp"]:
            res = send_email_smtp(
                kw["to"],
                subject,
                text,
                html,
                sender,
                files,
                bcc_recipients=kw["bcc"],
                cc_recipients=kw["cc"],
                exceptions=True,
            )
        elif kw["sendgrid"]:
            res = send_email_sendgrid(
                kw["to"],
                subject,
                text,
                html,
                sender,
                files,
                bcc_recipients=kw["bcc"],
                cc_recipients=kw["cc"],
                exceptions=True,
            )
        else:
            res = send_email(
                kw["to"],
                subject,
                text,
                html,
                sender,
                files,
                bcc_recipients=kw["bcc"],
                cc_recipients=kw["cc"],
                exceptions=True,
            )

        self.stdout.write("send_email returned {}".format(res))

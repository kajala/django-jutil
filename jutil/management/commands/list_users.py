from typing import List, Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import CommandParser
from django.utils.timezone import now

from jutil.command import SafeCommand
from jutil.email import send_email
from jutil.format import format_csv


class Command(SafeCommand):
    help = "Lists users in the system and their groups. Outputs CSV."

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--staff-only", action="store_true")
        parser.add_argument("--user-fields", type=str, default="id,username,first_name,last_name,email,is_active,is_staff,is_superuser,date_joined,last_login")
        parser.add_argument("--order-by", type=str, default="username")
        parser.add_argument("--bool-as-int", action="store_true")
        parser.add_argument("--false-as-empty", action="store_true")
        parser.add_argument("--totals", action="store_true")
        parser.add_argument("--email", type=str, help="Comma separated list of email addresses")

    @staticmethod
    def format_output(value: Any, bool_as_int: bool, false_as_empty: bool) -> Any:
        if not isinstance(value, bool):
            return value
        if not value and false_as_empty:
            return None
        if bool_as_int:
            return 1 if value else 0
        return bool(value)

    @staticmethod
    def count_totals(totals: List[Optional[int]], ix: int, value: Any):
        if isinstance(value, bool):
            if totals[ix] is None:
                totals[ix] = 0
            if value:
                totals[ix] += 1  # type: ignore

    def do(self, *args, **kwargs):  # pylint: disable=too-many-locals
        User = get_user_model()
        users = User.objects.all()
        if kwargs["staff_only"]:
            users = users.filter(is_staff=True)
        groups = Group.objects.all().order_by("name").distinct()
        group_names = list(groups.values_list("name", flat=True))
        group_list = list(groups)
        user_fields = kwargs["user_fields"].split(",")
        headers = user_fields + group_names
        rows: List[List[Any]] = [headers]  # type: ignore
        totals = [None] * len(headers)
        for user in users.order_by(*kwargs["order_by"].split(",")):
            row: List[Any] = []  # type: ignore
            ix = 0
            for k in user_fields:
                value = getattr(user, k)
                self.count_totals(totals, ix, value)
                row.append(self.format_output(value, bool_as_int=kwargs["bool_as_int"], false_as_empty=kwargs["false_as_empty"]))
                ix += 1
            for group in group_list:
                value = user.groups.filter(id=group.id).exists()
                self.count_totals(totals, ix, value)
                row.append(self.format_output(value, bool_as_int=kwargs["bool_as_int"], false_as_empty=kwargs["false_as_empty"]))
                ix += 1
            rows.append(row)
        if kwargs["totals"]:
            rows.append(totals)

        output = format_csv(rows)
        print(output)
        if kwargs["email"]:
            recipients = kwargs["email"].split(",")
            db_name = (settings.DATABASES.get("default") or {}).get("NAME") or ""  # type: ignore  # noqa
            base_name = f"{db_name}-users-{now().date()}"
            send_email(recipients, f"{db_name} users {now().date()}", "(CSV-file attached)", files_content=[(f"{base_name}.csv", output.encode())])
            print("Emailed user list to", recipients)

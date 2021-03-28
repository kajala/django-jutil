from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Q


class Command(BaseCommand):
    help = "Non-interactive user password reset"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("name", type=str)
        parser.add_argument("password", type=str)

    def handle(self, *args, **options):
        name = options["name"]
        passwd = options["password"]
        users = User.objects.filter(Q(username=name) | Q(email=name))
        if not users:
            self.stdout.write("User not found")
        for user in users:
            assert isinstance(user, User)
            user.set_password(passwd)
            user.save()
            self.stdout.write("User {} password set to {}".format(name, passwd))

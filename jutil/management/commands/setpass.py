from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Q


class Command(BaseCommand):
    help = "Non-interactive user password reset"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("name", type=str)
        parser.add_argument("password", type=str)
        parser.add_argument("--create-superuser", action="store_true")

    def handle(self, *args, **kwargs):
        name = kwargs["name"]
        passwd = kwargs["password"]
        users = list(get_user_model().objects.filter(Q(username=name) | Q(email=name)).distinct())
        if not users:
            self.stdout.write("User not found")
            if kwargs["create_superuser"]:
                user = get_user_model().objects.create_user(name, is_superuser=True, is_staff=True)
                self.stdout.write(f"Superuser {user} created")
                users = [user]
        for user in users:
            if not user.is_active:
                user.is_active = True
                self.stdout.write(f"User {user} set as active")
            user.set_password(passwd)
            user.save()
            self.stdout.write(f"User {user} password set")

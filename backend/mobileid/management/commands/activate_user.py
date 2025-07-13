from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Activate a user account"

    def add_arguments(self, parser):
        parser.add_argument(
            "username", type=str, help="The username of the user to activate"
        )

    def handle(self, *args, **options):
        username = options["username"]

        try:
            user = User.objects.get(username=username)

            if user.is_active:
                self.stdout.write(
                    self.style.WARNING(f"User {username} is already active")
                )
            else:
                user.is_active = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully activated user {username}")
                )

        except User.DoesNotExist:
            raise CommandError(f"User {username} does not exist")

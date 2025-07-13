from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Deactivate a user account"

    def add_arguments(self, parser):
        parser.add_argument(
            "username", type=str, help="The username of the user to deactivate"
        )

    def handle(self, *args, **options):
        username = options["username"]

        try:
            user = User.objects.get(username=username)

            if not user.is_active:
                self.stdout.write(
                    self.style.WARNING(f"User {username} is already disabled")
                )
            else:
                user.is_active = False
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully deactivated user {username}")
                )

        except User.DoesNotExist:
            raise CommandError(f"User {username} does not exist")

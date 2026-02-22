import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Creates or updates a superuser from environment variables."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not username or not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Missing DJANGO_SUPERUSER environment variables. "
                    "Skipping superuser creation."
                )
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                f'Superuser "{username}" already exists. Updating credentials...'
            )
            user = User.objects.get(username=username)
            user.set_password(password)
            user.email = email
            # Ensure superuser privileges are set
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Superuser "{username}" updated '
                    f"(password, email, is_staff=True, is_superuser=True)."
                )
            )
        else:
            self.stdout.write(f'Creating superuser "{username}"...')
            User.objects.create_superuser(
                username=username, email=email, password=password
            )
            msg = f'Superuser "{username}" created successfully.'
            self.stdout.write(self.style.SUCCESS(msg))

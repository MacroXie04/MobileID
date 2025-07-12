from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone


class Command(BaseCommand):
    help = 'List all disabled user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        disabled_users = User.objects.filter(is_active=False)
        
        if not disabled_users.exists():
            self.stdout.write(
                self.style.SUCCESS('No disabled user accounts')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {disabled_users.count()} disabled user accounts:')
        )
        
        for user in disabled_users:
            if options['verbose']:
                self.stdout.write(
                    f'Username: {user.username} | '
                    f'Email: {user.email or "None"} | '
                    f'Registration time: {user.date_joined.strftime("%Y-%m-%d %H:%M:%S")} | '
                    f'Last login: {user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else "Never logged in"}'
                )
            else:
                self.stdout.write(f'  - {user.username}') 
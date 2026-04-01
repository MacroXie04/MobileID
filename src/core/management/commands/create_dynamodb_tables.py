"""Management command to create all DynamoDB tables."""

from django.conf import settings
from django.core.management.base import BaseCommand

from core.dynamodb.tables import create_all_tables


class Command(BaseCommand):
    help = "Create all DynamoDB tables with GSIs and TTL configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-wait",
            action="store_true",
            help="Don't wait for tables to become ACTIVE",
        )

    def handle(self, *args, **options):
        self.stdout.write(f"Region: {settings.DYNAMODB_REGION}")
        self.stdout.write(
            f"Endpoint: {settings.DYNAMODB_ENDPOINT_URL or 'AWS default'}"
        )
        self.stdout.write(f"Table prefix: {settings.DYNAMODB_TABLE_PREFIX}")
        self.stdout.write("")

        wait = not options["no_wait"]
        created = create_all_tables(wait=wait)

        if created:
            for name in created:
                self.stdout.write(self.style.SUCCESS(f"  Created: {name}"))
        else:
            self.stdout.write(self.style.SUCCESS("All tables already exist."))

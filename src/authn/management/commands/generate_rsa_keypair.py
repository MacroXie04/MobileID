"""
Django management command to generate RSA key pairs for password encryption.

Usage:
    python manage.py generate_rsa_keypair
    python manage.py generate_rsa_keypair --key-size 4096
    python manage.py generate_rsa_keypair --keep-active  # Don't deactivate
                                                         # existing keys
"""

import logging

from authn.models import RSAKeyPair
from authn.utils.keys import clear_rsa_keypair_cache
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate a new RSA key pair for password encryption"

    def add_arguments(self, parser):
        parser.add_argument(
            "--key-size",
            type=int,
            choices=[2048, 4096],
            default=2048,
            help="RSA key size in bits (default: 2048)",
        )
        parser.add_argument(
            "--keep-active",
            action="store_true",
            help="Keep existing active keys active (don't deactivate them)",
        )

    def handle(self, *args, **options):
        key_size = options["key_size"]
        keep_active = options["keep_active"]

        self.stdout.write(f"Generating RSA-{key_size} key pair...")

        try:
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
            )
            public_key = private_key.public_key()

            # Serialize keys to PEM format
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")

            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")

            # Save to database
            with transaction.atomic():
                # Deactivate existing active keys unless --keep-active
                if not keep_active:
                    deactivated_count = RSAKeyPair.objects.filter(
                        is_active=True
                    ).update(is_active=False)
                    if deactivated_count > 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Deactivated {deactivated_count} "
                                f"existing active key pair(s)"
                            )
                        )

                # Create new key pair
                key_pair = RSAKeyPair.objects.create(
                    public_key=public_key_pem,
                    private_key=private_key_pem,
                    key_size=key_size,
                    is_active=True,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully created RSA-{key_size} key pair "
                        f"with ID: {key_pair.kid}"
                    )
                )
                self.stdout.write(f"Key ID: {key_pair.kid}")
                self.stdout.write("Status: ACTIVE")
                self.stdout.write(
                    f"Public key (first 50 chars): {public_key_pem[:50]}..."
                )

            # Clear cache to ensure new key is picked up immediately
            clear_rsa_keypair_cache()
            self.stdout.write(self.style.SUCCESS("Cleared RSA key pair cache"))

        except Exception as e:
            logger.exception("Failed to generate RSA key pair")
            raise CommandError(f"Failed to generate RSA key pair: {str(e)}")

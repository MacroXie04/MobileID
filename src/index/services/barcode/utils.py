import random

from django.utils import timezone


def _random_digits(length: int) -> str:
    """Return a random string of *length* numeric digits."""
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def _timestamp() -> str:
    """Return a timestamp string for dynamic barcodes."""
    return timezone.now().strftime("%Y%m%d%H%M%S")

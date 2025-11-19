import uuid

from django.contrib.auth.models import User
from django.db import models


# barcode information
class Barcode(models.Model):
    # storage upload user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # timestamp of creation
    time_created = models.DateTimeField(
        auto_now_add=True, null=True, verbose_name="time created"
    )

    # unique identifier for the barcode
    barcode_uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, null=True
    )

    # share with others option
    share_with_others = models.BooleanField(default=False)

    # barcode type (will be set up automatically)
    BARCODE_TYPE_CHOICES = [
        ("DynamicBarcode", "DynamicBarcode"),
        ("Identification", "Identification"),
        ("Others", "Others"),
    ]

    barcode_type = models.CharField(
        max_length=15,
        choices=BARCODE_TYPE_CHOICES,
        default="Others",
    )

    # barcode information
    barcode = models.CharField(max_length=120, unique=True)

    class Meta:
        app_label = "index"

    def __str__(self):
        if self.barcode_type == "DynamicBarcode":
            return f"Dynamic barcode ending with {self.barcode[-4:]}"
        elif self.barcode_type == "Identification":
            return f"{self.user.username}'s identification Barcode"
        return f"Barcode ending with {self.barcode[-4:]}"

from django.contrib.auth.models import User
from django.db import models


# barcode pull settings
class BarcodePullSettings(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Barcode pull gender choices
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Unknow", "Unknow"),
    ]
    gender_setting = models.CharField(max_length=10, choices=GENDER_CHOICES, default="Unknow")


# barcode total usage
class BarcodeUsage(models.Model):
    # foreign key to barcode
    barcode = models.ForeignKey("Barcode", on_delete=models.CASCADE)

    # total usage count
    total_usage = models.PositiveIntegerField(default=0)

    # total usage limit
    total_usage_limit = models.PositiveIntegerField(default=0)

    # daily usage limit (0 means no limit)
    daily_usage_limit = models.PositiveIntegerField(default=0)

    # last used timestamp
    last_used = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Barcode ending with {self.barcode.barcode[-4:]} - Total Usage: {self.total_usage} - Last Used: {self.last_used}"

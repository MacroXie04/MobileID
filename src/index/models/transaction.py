from django.contrib.auth.models import User
from django.db import models


class Transaction(models.Model):
    # foreign key to user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # usage detail
    barcode_used = models.ForeignKey("Barcode", default=None, on_delete=models.SET_NULL, null=True)
    time_created = models.DateTimeField(auto_now_add=True, null=True, verbose_name="time used")



from django.contrib.auth.models import User
from django.db import models


# user information
class StudentInformation(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # student information
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=100)
    user_profile_img = models.TextField()

    def __str__(self):
        return f"{self.name} - StudentID: **{self.student_id[-4:]}"


# user barcode usage
class UserBarcodeUsage(models.Model):
    # foreign key to user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # barcode usage
    barcode = models.ForeignKey('Barcode', on_delete=models.CASCADE)

    # timestamp of usage
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} used barcode {self.barcode.barcode[-4:]} at {self.timestamp}"

# barcode total usage
class BarcodeUsage(models.Model):
    # foreign key to barcode
    barcode = models.ForeignKey('Barcode', on_delete=models.CASCADE)

    # total usage count
    total_usage = models.PositiveIntegerField(default=0)

    # last used timestamp
    last_used = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Barcode ending with {self.barcode.barcode[-4:]} - Total Usage: {self.total_usage} - Last Used: {self.last_used}"

# barcode information
class Barcode(models.Model):
    # storage upload user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # barcode type (will be setup automatically)
    BARCODE_TYPE_CHOICES = [
        ('Dynamic', 'Dynamic'),
        ('Static', 'Static'),
    ]

    barcode_type = models.CharField(
        max_length=10,
        choices=BARCODE_TYPE_CHOICES,
        default='Static',
    )

    # barcode information
    barcode = models.TextField()
    student_id = models.CharField(max_length=100, blank=True, null=True, default=None)

    # server verification information
    session = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.barcode_type} barcode ending with {self.barcode[-4:]}"


# user barcode settings
class UserBarcodeSettings(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # barcode settings
    barcode = models.ForeignKey(Barcode, on_delete=models.SET_NULL, blank=True, null=True)

    # server verification settings
    server_verification = models.BooleanField(default=False)

    # timestamp verification
    timestamp_verification = models.BooleanField(default=True)

    # barcode pull settings
    barcode_pull = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Barcode Settings"


# transfer information
class Transfer(models.Model):
    cookie = models.TextField()
    unique_code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"**{self.unique_code[-4:]} - cookie: *{self.cookie[-4:]}"

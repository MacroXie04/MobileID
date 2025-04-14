import os
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


# function to generate a unique file path for user uploads
def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{instance.user.username}_{uuid.uuid4().hex}.{ext}"
    return os.path.join('avatars', unique_filename)


# user passkeys
class PasskeyCredential(models.Model):
    # foreign key to user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='passkey_credentials',
    )

    # passkey information
    credential_id = models.CharField(max_length=256, unique=True)
    public_key = models.TextField()
    sign_count = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Passkey ending with {self.credential_id[-4:]} for user {self.user.username}"


# user information
class StudentInformation(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # student information
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to=user_directory_path, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - StudentID: **{self.student_id[-4:]}"


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

    # usage information
    total_usage = models.IntegerField(default=0)
    last_used = models.DateTimeField(auto_now=False)

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

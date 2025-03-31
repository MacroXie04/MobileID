import os
import uuid

from django.contrib.auth.models import User
from django.db import models


# function to generate a unique file path for user uploads
def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{instance.user.username}_{uuid.uuid4().hex}.{ext}"
    return os.path.join('avatars', unique_filename)


# user information
class StudentInformation(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # student information
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=100)
    session = models.TextField()

    # user upload photo
    avatar = models.ImageField(upload_to=user_directory_path, blank=True, null=True)

    # mobile id information
    mobile_id_rand_array = models.JSONField(default=list, blank=True)
    current_mobile_id_rand = models.IntegerField(default=0, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    code_student_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


# user barcode settings
class UserBarcodeSettings(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # barcode settings
    barcode_status = models.BooleanField(default=False)
    static_barcode = models.CharField(max_length=100, blank=True)

    # server verification settings
    server_verification = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.barcode_status}"


# transfer information
class Transfer(models.Model):
    cookie = models.TextField()
    unique_code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

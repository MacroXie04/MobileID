from django.db import models
from django.contrib.auth.models import User

class StudentInformation(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # student information
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=100)
    section = models.TextField()

    # mobile id information
    mobile_id_rand_array = models.JSONField(default=list, blank=True)
    current_mobile_id_rand = models.IntegerField(default=0, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    code_student_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Transfer(models.Model):
    cookie = models.TextField()
    unique_code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
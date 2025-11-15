import uuid

from django.contrib.auth.models import User
from django.db import models


# user information
class UserProfile(models.Model):
    # foreign key to user
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # information
    name = models.CharField(max_length=100)
    information_id = models.CharField(max_length=100)

    # user uuid
    profile_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # user profile image (base64 encoded png 128*128)
    user_profile_img = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "Base64 encoded PNG of the user's 128*128 avatar. " "No data-URI prefix."
        ),
        verbose_name="avatar (Base64)",
    )

    def __str__(self):
        return f"{self.name} - ID: **{self.information_id[-4:]}"


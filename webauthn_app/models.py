from django.contrib.auth.models import User
from django.db import models


class PasskeyCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    credential_id = models.CharField(max_length=512, unique=True)
    public_key = models.TextField()
    sign_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Credential"

from django.contrib.auth.models import User
from django.db import models


class PasskeyCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passkeys')
    credential_id = models.BinaryField(unique=True)
    public_key = models.BinaryField()
    sign_count = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        created_str = self.created_at.strftime("%Y-%m-%d")
        return f"{self.user.username}'s Passkey - Created on {created_str}"

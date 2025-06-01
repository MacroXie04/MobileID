from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    # foreign key link the user model
    user = models.OneToOneField(User, on_delete=models.CASCADE)




class PasskeyCredential(models.Model):
    # foreign key link the user model
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passkeys')

    # passkey credential fields
    credential_id = models.BinaryField(unique=True)
    public_key = models.BinaryField()

    # sign count for the passkey
    sign_count = models.BigIntegerField(default=0)

    # timestamp for when the passkey was created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        created_str = self.created_at.strftime("%Y-%m-%d")
        return f"{self.user.username}'s Passkey - Created on {created_str}"

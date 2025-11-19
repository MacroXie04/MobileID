from django.db import models


# request status from OIT server
class ServerSystemStatus(models.Model):
    # request time
    request_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        app_label = "index"

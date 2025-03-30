from django.contrib import admin
from .models import StudentInformation, Transfer, UserBarcodeSettings

admin.site.register(StudentInformation)
admin.site.register(Transfer)
admin.site.register(UserBarcodeSettings)
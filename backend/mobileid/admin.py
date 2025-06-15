from django.contrib import admin
from .models import StudentInformation, Transfer, UserBarcodeSettings, Barcode

admin.site.register(StudentInformation)
admin.site.register(UserBarcodeSettings)
admin.site.register(Transfer)
admin.site.register(Barcode)


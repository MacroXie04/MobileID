from django.contrib import admin
from .models import StudentInformation, UserBarcodeSettings, Barcode, Transfer

admin.site.site_header = "MobileID Admin"
admin.site.site_title = "MobileID Admin Portal"

admin.site.register(StudentInformation)
admin.site.register(UserBarcodeSettings)
admin.site.register(Barcode)
admin.site.register(Transfer)

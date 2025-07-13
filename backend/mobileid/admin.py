from django.contrib import admin
from .models import UserProfile, UserBarcodeSettings, Barcode

admin.site.site_header = "MobileID Admin"
admin.site.site_title = "MobileID Admin Portal"

admin.site.register(UserProfile)
admin.site.register(UserBarcodeSettings)
admin.site.register(Barcode)

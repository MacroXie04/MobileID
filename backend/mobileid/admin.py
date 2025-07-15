from django.contrib import admin

from .models import Barcode, UserBarcodeSettings, UserProfile, UserAccount, UserBarcodeUsageHistory

admin.site.site_header = "MobileID Admin"
admin.site.site_title = "MobileID Admin Portal"

admin.site.register(UserAccount)
admin.site.register(UserBarcodeUsageHistory)

admin.site.register(UserProfile)
admin.site.register(UserBarcodeSettings)
admin.site.register(Barcode)

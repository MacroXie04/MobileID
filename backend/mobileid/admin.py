from django.contrib import admin

from .models import Barcode, UserBarcodeSettings, BarcodeUsage

admin.site.site_header = "MobileID Admin"
admin.site.site_title = "MobileID Admin Portal"


class BarcodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'barcode_type', 'time_created', 'barcode_uuid']
    readonly_fields = ['time_created', 'barcode_uuid']


class UserBarcodeSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'barcode', 'server_verification', 'barcode_pull']


class BarcodeUsageAdmin(admin.ModelAdmin):
    list_display = ['barcode', 'total_usage', 'last_used']


admin.site.register(Barcode, BarcodeAdmin)
admin.site.register(UserBarcodeSettings, UserBarcodeSettingsAdmin)
admin.site.register(BarcodeUsage, BarcodeUsageAdmin)

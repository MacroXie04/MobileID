from django.contrib import admin

from .models import Barcode, UserBarcodeSettings, UserProfile, UserAccount, UserBarcodeUsageHistory, BarcodeUsage

admin.site.site_header = "MobileID Admin"
admin.site.site_title = "MobileID Admin Portal"

class BarcodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'barcode_type', 'time_created', 'barcode_uuid']
    readonly_fields = ['time_created', 'barcode_uuid']

class UserAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_type']

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'information_id']

class UserBarcodeSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'barcode', 'server_verification', 'timestamp_verification', 'barcode_pull']

class UserBarcodeUsageHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'barcode', 'timestamp']

class BarcodeUsageAdmin(admin.ModelAdmin):
    list_display = ['barcode', 'total_usage', 'last_used']

admin.site.register(Barcode, BarcodeAdmin)
admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(UserBarcodeUsageHistory, UserBarcodeUsageHistoryAdmin)
admin.site.register(UserBarcodeSettings, UserBarcodeSettingsAdmin)
admin.site.register(BarcodeUsage, BarcodeUsageAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
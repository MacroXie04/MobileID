from django.contrib import admin

# Admin site configuration
admin.site.site_header = "MobileID Admin"
admin.site.site_title = "MobileID Admin Portal"
admin.site.index_title = "Administration"
admin.site.empty_value_display = "—"

# Note: Index app models have been migrated to DynamoDB.
# Django admin registrations for barcode, transaction, and settings models
# have been removed. These are now managed via the API.

from django.contrib import admin

# Admin site configuration
admin.site.site_header = "MobileID Admin"
admin.site.site_title = "MobileID Admin Portal"
admin.site.index_title = "Administration"
admin.site.empty_value_display = "—"

# Import all admin classes so @admin.register() decorators execute
from .barcode import BarcodeAdmin  # noqa: F401, E402
from .barcode_usage import BarcodeUsageAdmin  # noqa: F401, E402
from .user_settings import (
    UserBarcodeSettingsAdmin,
    UserBarcodePullSettingsAdmin,
)  # noqa: F401, E402
from .barcode_profile import BarcodeUserProfileAdmin  # noqa: F401, E402
from .transaction import TransactionAdmin  # noqa: F401, E402

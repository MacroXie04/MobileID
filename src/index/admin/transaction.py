from django.contrib import admin

from ..models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model"""

    list_display = (
        "id",
        "user",
        "barcode_display",
        "barcode_owner",
        "barcode_type",
        "time_created",
    )
    list_filter = ("barcode_used__barcode_type", "user")
    search_fields = (
        "user__username",
        "user__email",
        "barcode_used__barcode",
    )
    ordering = ("-time_created",)
    readonly_fields = ("time_created",)
    list_display_links = ("id", "user", "barcode_display")
    list_per_page = 50
    list_select_related = ("user", "barcode_used")
    autocomplete_fields = ["user", "barcode_used"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "barcode_used")

    @admin.display(description="Barcode")
    def barcode_display(self, obj):
        if obj.barcode_used:
            try:
                return f"...{obj.barcode_used.barcode[-4:]}"
            except Exception:
                return "-"
        return "-"

    @admin.display(description="Type", ordering="barcode_used__barcode_type")
    def barcode_type(self, obj):
        if obj.barcode_used:
            return obj.barcode_used.barcode_type
        return "-"

    @admin.display(description="Barcode Owner")
    def barcode_owner(self, obj):
        b = obj.barcode_used
        if not b:
            return "-"
        # If a profile is linked to this barcode, use its name; otherwise fall
        # back to username
        try:
            profile = b.barcodeuserprofile
            if profile and profile.name:
                return profile.name
        except Exception:
            pass
        return b.user.username

    @admin.display(description="Barcode Name")
    def barcode_name(self, obj):
        """Human-readable name for the related barcode."""
        b = obj.barcode_used
        if not b:
            return "-"
        if b.barcode_type == "Identification":
            return f"{b.user.username}'s identification barcode"
        if b.barcode_type == "DynamicBarcode":
            return f"Dynamic Barcode ending with {b.barcode[-4:]}"
        return f"Barcode ending with {b.barcode[-4:]}"

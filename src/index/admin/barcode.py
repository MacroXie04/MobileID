from django.contrib import admin
from django.utils.html import format_html

from .inlines import BarcodeUsageInline, BarcodeUserProfileInline
from ..models import Barcode


@admin.register(Barcode)
class BarcodeAdmin(admin.ModelAdmin):
    """Admin configuration for Barcode model"""

    list_display = (
        "barcode_display",
        "barcode_type",
        "user",
        "time_created",
        "barcode_uuid_display",
        "usage_count",
    )
    list_filter = ("barcode_type", "user")
    search_fields = (
        "barcode",
        "barcode_uuid",
        "user__username",
        "user__email",
    )
    readonly_fields = ("barcode_uuid", "time_created", "barcode_display_full")
    # Commented out date_hierarchy to avoid timezone issues
    # date_hierarchy = 'time_created'
    ordering = ("-time_created",)
    list_display_links = ("barcode_display",)
    list_per_page = 50
    list_max_show_all = 200
    list_select_related = ("user",)
    save_on_top = True
    autocomplete_fields = ["user"]

    fieldsets = (
        (
            "Barcode Information",
            {
                "fields": (
                    "barcode",
                    "barcode_display_full",
                    "barcode_type",
                    "barcode_uuid",
                )
            },
        ),
        ("User & Timestamps", {"fields": ("user", "time_created")}),
    )

    inlines = [BarcodeUsageInline, BarcodeUserProfileInline]

    @admin.display(description="Barcode")
    def barcode_display(self, obj):
        """Display only last 4 digits of barcode"""
        return format_html("<strong>...{}</strong>", obj.barcode[-4:])

    @admin.display(description="Full Barcode")
    def barcode_display_full(self, obj):
        """Display full barcode in monospace font"""
        return format_html("<code>{}</code>", obj.barcode)

    @admin.display(description="UUID")
    def barcode_uuid_display(self, obj):
        """Display UUID in a more readable format"""
        return format_html(
            "<code>{}</code>", str(obj.barcode_uuid)[:8] + "..."
        )

    @admin.display(
        description="Total Usage", ordering="barcodeusage__total_usage"
    )
    def usage_count(self, obj):
        """Display total usage count from related BarcodeUsage"""
        try:
            usage = obj.barcodeusage_set.first()
            if usage:
                return format_html(
                    '<span style="color: {};">{}</span>',
                    "green" if usage.total_usage > 0 else "gray",
                    usage.total_usage,
                )
        except Exception:
            return format_html('<span style="color: gray;">0</span>')
        return format_html('<span style="color: gray;">0</span>')

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return (
            super()
            .get_queryset(request)
            .select_related("user")
            .prefetch_related("barcodeusage_set")
        )

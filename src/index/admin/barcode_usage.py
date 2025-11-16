from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from ..models import BarcodeUsage


@admin.register(BarcodeUsage)
class BarcodeUsageAdmin(admin.ModelAdmin):
    """Admin configuration for BarcodeUsage model"""

    list_display = (
        "barcode_display",
        "user_display",
        "total_usage",
        "last_used_display",
        "usage_status",
        "barcode_type",
    )
    list_filter = ("barcode__barcode_type",)  # Removed 'last_used' from filter
    search_fields = ("barcode__barcode", "barcode__user__username")
    readonly_fields = ("last_used",)
    # Commented out date_hierarchy to avoid timezone issues
    # date_hierarchy = 'last_used'
    ordering = ("-last_used",)
    list_per_page = 50
    list_select_related = ("barcode", "barcode__user")
    show_full_result_count = False

    fieldsets = (
        ("Barcode Information", {"fields": ("barcode",)}),
        ("Usage Statistics", {"fields": ("total_usage", "last_used")}),
    )

    @admin.display(description="Barcode")
    def barcode_display(self, obj):
        """Display barcode ending"""
        if obj.barcode.barcode_type == "Identification":
            return f"{obj.barcode.user.username}'s identification barcode"
        if obj.barcode.barcode_type == "DynamicBarcode":
            return f"dynamic barcode ending with {obj.barcode.barcode[-4:]}"
        if obj.barcode.barcode_type == "Others":
            return f"barcode ending with {obj.barcode.barcode[-4:]}"
        return "-"

    @admin.display(description="Type", ordering="barcode__barcode_type")
    def barcode_type(self, obj):
        """Display the barcode type"""
        return obj.barcode.barcode_type

    @admin.display(description="User", ordering="barcode__user__username")
    def user_display(self, obj):
        """Display the user name"""
        return obj.barcode.user.username

    @admin.display(description="Last Used", ordering="last_used")
    def last_used_display(self, obj):
        """Display last used time with proper timezone handling"""
        if not obj.last_used:
            return "Never"
        try:
            dt = obj.last_used
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            dt = timezone.localtime(dt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "N/A"

    @admin.display(description="Status")
    def usage_status(self, obj):
        """Display usage status with color coding"""
        if obj.total_usage == 0:
            return format_html('<span style="color: gray;">Unused</span>')
        if obj.total_usage < 10:
            return format_html('<span style="color: orange;">Low Usage</span>')
        if obj.total_usage < 50:
            return format_html('<span style="color: blue;">Moderate Usage</span>')
        return format_html('<span style="color: green;">High Usage</span>')

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related("barcode", "barcode__user")

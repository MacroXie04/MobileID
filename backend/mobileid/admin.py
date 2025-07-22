from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from mobileid.models import Barcode, UserBarcodeSettings, BarcodeUsage

admin.site.site_header = "Barcode Manager Admin"
admin.site.site_title = "MobileID Admin Portal"


class BarcodeUsageInline(admin.TabularInline):
    """Inline admin for BarcodeUsage to display within Barcode admin"""
    model = BarcodeUsage
    extra = 0
    readonly_fields = ('total_usage', 'last_used')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Barcode)
class BarcodeAdmin(admin.ModelAdmin):
    """Admin configuration for Barcode model"""
    list_display = (
        'barcode_display',
        'barcode_type',
        'user',
        'time_created',
        'barcode_uuid_display',
        'usage_count'
    )
    list_filter = ('barcode_type', 'user')  # Removed 'time_created' from filter
    search_fields = ('barcode', 'barcode_uuid', 'user__username', 'user__email')
    readonly_fields = ('barcode_uuid', 'time_created', 'barcode_display_full')
    # Commented out date_hierarchy to avoid timezone issues
    # date_hierarchy = 'time_created'
    ordering = ('-time_created',)

    fieldsets = (
        ('Barcode Information', {
            'fields': ('barcode', 'barcode_display_full', 'barcode_type', 'barcode_uuid')
        }),
        ('User & Timestamps', {
            'fields': ('user', 'time_created')
        }),
        ('Server Verification', {
            'fields': ('session',),
            'classes': ('collapse',)
        }),
    )

    inlines = [BarcodeUsageInline]

    def barcode_display(self, obj):
        """Display only last 4 digits of barcode"""
        return format_html(
            '<strong>...{}</strong>',
            obj.barcode[-4:]
        )

    barcode_display.short_description = 'Barcode'

    def barcode_display_full(self, obj):
        """Display full barcode in monospace font"""
        return format_html('<code>{}</code>', obj.barcode)

    barcode_display_full.short_description = 'Full Barcode'

    def barcode_uuid_display(self, obj):
        """Display UUID in a more readable format"""
        return format_html('<code>{}</code>', str(obj.barcode_uuid)[:8] + '...')

    barcode_uuid_display.short_description = 'UUID'

    def usage_count(self, obj):
        """Display total usage count from related BarcodeUsage"""
        try:
            usage = obj.barcodeusage_set.first()
            if usage:
                return format_html(
                    '<span style="color: {};">{}</span>',
                    'green' if usage.total_usage > 0 else 'gray',
                    usage.total_usage
                )
        except:
            pass
        return format_html('<span style="color: gray;">0</span>')

    usage_count.short_description = 'Total Usage'
    usage_count.admin_order_field = 'barcodeusage__total_usage'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user').prefetch_related('barcodeusage_set')


@admin.register(BarcodeUsage)
class BarcodeUsageAdmin(admin.ModelAdmin):
    """Admin configuration for BarcodeUsage model"""
    list_display = (
        'barcode_display',
        'total_usage',
        'last_used_display',
        'usage_status',
        'barcode_type'
    )
    list_filter = ('barcode__barcode_type',)  # Removed 'last_used' from filter
    search_fields = ('barcode__barcode', 'barcode__user__username')
    readonly_fields = ('last_used',)
    # Commented out date_hierarchy to avoid timezone issues
    # date_hierarchy = 'last_used'
    ordering = ('-last_used',)

    fieldsets = (
        ('Barcode Information', {
            'fields': ('barcode',)
        }),
        ('Usage Statistics', {
            'fields': ('total_usage', 'last_used')
        }),
    )

    def barcode_display(self, obj):
        """Display barcode ending"""
        return f"...{obj.barcode.barcode[-4:]}"

    barcode_display.short_description = 'Barcode'

    def barcode_type(self, obj):
        """Display the barcode type"""
        return obj.barcode.barcode_type

    barcode_type.short_description = 'Type'
    barcode_type.admin_order_field = 'barcode__barcode_type'

    def last_used_display(self, obj):
        """Display last used time with proper timezone handling"""
        if obj.last_used:
            try:
                # Ensure timezone awareness
                if timezone.is_aware(obj.last_used):
                    return obj.last_used.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    return timezone.make_aware(obj.last_used).strftime('%Y-%m-%d %H:%M:%S')
            except:
                return 'N/A'
        return 'Never'

    last_used_display.short_description = 'Last Used'
    last_used_display.admin_order_field = 'last_used'

    def usage_status(self, obj):
        """Display usage status with color coding"""
        if obj.total_usage == 0:
            return format_html('<span style="color: gray;">Unused</span>')
        elif obj.total_usage < 10:
            return format_html('<span style="color: orange;">Low Usage</span>')
        elif obj.total_usage < 50:
            return format_html('<span style="color: blue;">Moderate Usage</span>')
        else:
            return format_html('<span style="color: green;">High Usage</span>')

    usage_status.short_description = 'Status'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('barcode', 'barcode__user')


@admin.register(UserBarcodeSettings)
class UserBarcodeSettingsAdmin(admin.ModelAdmin):
    """Admin configuration for UserBarcodeSettings model"""
    list_display = (
        'user',
        'barcode_display',
        'server_verification',
        'barcode_pull',
        'settings_status'
    )
    list_filter = ('server_verification', 'barcode_pull')
    search_fields = ('user__username', 'user__email', 'barcode__barcode')
    raw_id_fields = ('user', 'barcode')

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Barcode Configuration', {
            'fields': ('barcode',)
        }),
        ('Settings', {
            'fields': ('server_verification', 'barcode_pull'),
            'description': 'Configure barcode behavior for this user'
        }),
    )

    def barcode_display(self, obj):
        """Display associated barcode or 'Not Set'"""
        if obj.barcode:
            return format_html(
                '<span style="color: green;">...{}</span>',
                obj.barcode.barcode[-4:]
            )
        return format_html('<span style="color: gray;">Not Set</span>')

    barcode_display.short_description = 'Barcode'

    def settings_status(self, obj):
        """Display overall settings status"""
        if obj.barcode and obj.server_verification:
            return format_html('<span style="color: green;">Fully Configured</span>')
        elif obj.barcode:
            return format_html('<span style="color: orange;">Partially Configured</span>')
        else:
            return format_html('<span style="color: red;">Not Configured</span>')

    settings_status.short_description = 'Status'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'barcode')

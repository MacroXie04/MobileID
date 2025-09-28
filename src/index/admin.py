from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
import json
from index.models import (
    Barcode,
    UserBarcodeSettings,
    BarcodeUsage,
    BarcodeUserProfile,
    Transaction,
)

admin.site.site_header = "MobileID Admin"
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
    list_filter = ('barcode_type', 'user')
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
        'user_display',
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

        if obj.barcode.barcode_type == "Identification":
            # display user name and last 4 digits
            return f"{obj.barcode.user.username}'s identification barcode"
        if obj.barcode.barcode_type == "DynamicBarcode":
            # display barcode type and last 4 digits
            return f"dynamic barcode ending with {obj.barcode.barcode[-4:]}"
        if obj.barcode.barcode_type == "Others":
            # display barcode type and last 4 digits
            return f"barcode ending with {obj.barcode.barcode[-4:]}"

    barcode_display.short_description = 'Barcode'

    def barcode_type(self, obj):
        """Display the barcode type"""
        return obj.barcode.barcode_type

    barcode_type.short_description = 'Type'
    barcode_type.admin_order_field = 'barcode__barcode_type'

    def user_display(self, obj):
        """Display the user name"""
        return obj.barcode.user.username

    user_display.short_description = 'User'
    user_display.admin_order_field = 'barcode__user__username'

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
    list_display = ('user', 'barcode', 'server_verification', 'associate_user_profile_with_barcode')
    list_filter = ('server_verification', 'associate_user_profile_with_barcode')
    search_fields = ('user__username', 'barcode__barcode')
    ordering = ('user__username',)
    autocomplete_fields = ['user', 'barcode']

    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Settings', {
            'fields': ('barcode', 'server_verification', 'associate_user_profile_with_barcode')
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'barcode')


@admin.register(BarcodeUserProfile)
class BarcodeUserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for BarcodeUserProfile model"""
    list_display = ('linked_barcode_display', 'name', 'information_id', 'avatar_preview')
    search_fields = ('name', 'information_id', 'linked_barcode__barcode', 'linked_barcode__user__username')
    readonly_fields = ('avatar_preview',)
    ordering = ('name',)

    fieldsets = (
        ('Profile', {
            'fields': ('linked_barcode', 'name', 'information_id')
        }),
        ('Avatar (PNG base64 128x128)', {
            'fields': ('user_profile_img', 'avatar_preview')
        }),
    )

    def linked_barcode_display(self, obj):
        try:
            return f"...{obj.linked_barcode.barcode[-4:]} ({obj.linked_barcode.barcode_type})"
        except Exception:
            return '-'

    linked_barcode_display.short_description = 'Linked Barcode'

    def avatar_preview(self, obj):
        if obj.user_profile_img:
            return format_html(
                '<img src="data:image/png;base64,{}" style="height:64px;width:64px;border-radius:8px;object-fit:cover;" />',
                obj.user_profile_img
            )
        return '-'

    avatar_preview.short_description = 'Avatar'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model"""
    list_display = (
        'id',
        'user',
        'barcode_display',
        'barcode_type',
        'time_created',
    )
    list_filter = ('barcode_used__barcode_type', 'user')
    search_fields = (
        'user__username',
        'user__email',
        'barcode_used__barcode',
    )
    ordering = ('-time_created',)
    readonly_fields = ('time_created',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('user', 'barcode_used')
        )

    def barcode_display(self, obj):
        if obj.barcode_used:
            try:
                return f"...{obj.barcode_used.barcode[-4:]}"
            except Exception:
                return '-'
        return '-'

    barcode_display.short_description = 'Barcode'

    def barcode_type(self, obj):
        if obj.barcode_used:
            return obj.barcode_used.barcode_type
        return '-'

    barcode_type.short_description = 'Type'
    barcode_type.admin_order_field = 'barcode_used__barcode_type'


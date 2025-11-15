from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import (
    Barcode,
    UserBarcodeSettings,
    UserBarcodePullSettings,
    BarcodeUsage,
    BarcodeUserProfile,
    Transaction,
)

admin.site.site_header = "MobileID Admin"
admin.site.site_title = "MobileID Admin Portal"
admin.site.index_title = "Administration"
admin.site.empty_value_display = "—"


class BarcodeUsageInline(admin.TabularInline):
    """Inline admin for BarcodeUsage to display within Barcode admin"""
    model = BarcodeUsage
    extra = 0
    readonly_fields = ('total_usage', 'last_used')
    can_delete = False
    show_change_link = True


class BarcodeUserProfileInline(admin.TabularInline):
    """Inline admin for BarcodeUserProfile linked to a Barcode"""
    model = BarcodeUserProfile
    fk_name = 'linked_barcode'
    extra = 0
    readonly_fields = ('avatar_preview',)
    can_delete = True
    show_change_link = True
    fields = ('name', 'information_id', 'user_profile_img', 'avatar_preview')

    @admin.display(description='Avatar')
    def avatar_preview(self, obj):
        if obj and getattr(obj, 'user_profile_img', None):
            return format_html(
                '<img src="data:image/png;base64,{}" style="height:64px;width:64px;border-radius:8px;object-fit:cover;" />',
                obj.user_profile_img
            )
        return '-'

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
    list_display_links = ('barcode_display',)
    list_per_page = 50
    list_max_show_all = 200
    list_select_related = ('user',)
    save_on_top = True
    autocomplete_fields = ['user']

    fieldsets = (
        ('Barcode Information', {
            'fields': ('barcode', 'barcode_display_full', 'barcode_type', 'barcode_uuid')
        }),
        ('User & Timestamps', {
            'fields': ('user', 'time_created')
        }),
    )

    inlines = [BarcodeUsageInline, BarcodeUserProfileInline]

    @admin.display(description='Barcode')
    def barcode_display(self, obj):
        """Display only last 4 digits of barcode"""
        return format_html('<strong>...{}</strong>', obj.barcode[-4:])

    @admin.display(description='Full Barcode')
    def barcode_display_full(self, obj):
        """Display full barcode in monospace font"""
        return format_html('<code>{}</code>', obj.barcode)

    @admin.display(description='UUID')
    def barcode_uuid_display(self, obj):
        """Display UUID in a more readable format"""
        return format_html('<code>{}</code>', str(obj.barcode_uuid)[:8] + '...')

    @admin.display(description='Total Usage', ordering='barcodeusage__total_usage')
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
        except Exception:
            return format_html('<span style="color: gray;">0</span>')
        return format_html('<span style="color: gray;">0</span>')

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
    list_per_page = 50
    list_select_related = ('barcode', 'barcode__user')
    show_full_result_count = False

    fieldsets = (
        ('Barcode Information', {
            'fields': ('barcode',)
        }),
        ('Usage Statistics', {
            'fields': ('total_usage', 'last_used')
        }),
    )

    @admin.display(description='Barcode')
    def barcode_display(self, obj):
        """Display barcode ending"""
        if obj.barcode.barcode_type == "Identification":
            return f"{obj.barcode.user.username}'s identification barcode"
        if obj.barcode.barcode_type == "DynamicBarcode":
            return f"dynamic barcode ending with {obj.barcode.barcode[-4:]}"
        if obj.barcode.barcode_type == "Others":
            return f"barcode ending with {obj.barcode.barcode[-4:]}"
        return "-"

    @admin.display(description='Type', ordering='barcode__barcode_type')
    def barcode_type(self, obj):
        """Display the barcode type"""
        return obj.barcode.barcode_type

    @admin.display(description='User', ordering='barcode__user__username')
    def user_display(self, obj):
        """Display the user name"""
        return obj.barcode.user.username

    @admin.display(description='Last Used', ordering='last_used')
    def last_used_display(self, obj):
        """Display last used time with proper timezone handling"""
        if not obj.last_used:
            return 'Never'
        try:
            dt = obj.last_used
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            dt = timezone.localtime(dt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return 'N/A'

    @admin.display(description='Status')
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
        return super().get_queryset(request).select_related('barcode', 'barcode__user')


@admin.register(UserBarcodeSettings)
class UserBarcodeSettingsAdmin(admin.ModelAdmin):
    """Admin configuration for UserBarcodeSettings model"""
    list_display = ('user', 'barcode', 'server_verification', 'associate_user_profile_with_barcode')
    list_filter = ('server_verification', 'associate_user_profile_with_barcode')
    search_fields = ('user__username', 'barcode__barcode')
    ordering = ('user__username',)
    autocomplete_fields = ['user', 'barcode']
    list_per_page = 50
    list_select_related = ('user', 'barcode')
    show_full_result_count = False
    save_on_top = True

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


@admin.register(UserBarcodePullSettings)
class UserBarcodePullSettingsAdmin(admin.ModelAdmin):
    """Admin configuration for UserBarcodePullSettings model"""
    list_display = ('user', 'pull_setting', 'gender_setting')
    list_filter = ('pull_setting', 'gender_setting')
    search_fields = ('user__username', 'user__email')
    ordering = ('user__username',)
    autocomplete_fields = ['user']
    list_per_page = 50
    list_select_related = ('user',)
    show_full_result_count = False
    save_on_top = True

    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Pull Settings', {
            'fields': ('pull_setting', 'gender_setting')
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(BarcodeUserProfile)
class BarcodeUserProfileAdmin(admin.ModelAdmin):
    """Admin configuration for BarcodeUserProfile model"""
    list_display = ('linked_barcode_display', 'name', 'information_id', 'avatar_preview')
    search_fields = ('name', 'information_id', 'linked_barcode__barcode', 'linked_barcode__user__username')
    readonly_fields = ('avatar_preview',)
    ordering = ('name',)
    list_per_page = 50
    save_on_top = True

    fieldsets = (
        ('Profile', {
            'fields': ('linked_barcode', 'name', 'information_id')
        }),
        ('Avatar (PNG base64 128x128)', {
            'fields': ('user_profile_img', 'avatar_preview')
        }),
    )

    @admin.display(description='Linked Barcode')
    def linked_barcode_display(self, obj):
        try:
            return f"...{obj.linked_barcode.barcode[-4:]} ({obj.linked_barcode.barcode_type})"
        except Exception:
            return '-'

    @admin.display(description='Avatar')
    def avatar_preview(self, obj):
        if obj.user_profile_img:
            return format_html(
                '<img src="data:image/png;base64,{}" style="height:64px;width:64px;border-radius:8px;object-fit:cover;" />',
                obj.user_profile_img
            )
        return '-'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model"""
    list_display = (
        'id',
        'user',
        'barcode_display',
        'barcode_owner',
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
    list_display_links = ('id', 'user', 'barcode_display')
    list_per_page = 50
    list_select_related = ('user', 'barcode_used')
    autocomplete_fields = ['user', 'barcode_used']

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('user', 'barcode_used')
        )

    @admin.display(description='Barcode')
    def barcode_display(self, obj):
        if obj.barcode_used:
            try:
                return f"...{obj.barcode_used.barcode[-4:]}"
            except Exception:
                return '-'
        return '-'

    @admin.display(description='Type', ordering='barcode_used__barcode_type')
    def barcode_type(self, obj):
        if obj.barcode_used:
            return obj.barcode_used.barcode_type
        return '-'

    @admin.display(description='Barcode Owner')
    def barcode_owner(self, obj):
        b = obj.barcode_used
        if not b:
            return '-'
        # If a profile is linked to this barcode, use its name; otherwise fall back to username
        try:
            profile = b.barcodeuserprofile
            if profile and profile.name:
                return profile.name
        except Exception:
            pass
        return b.user.username

    @admin.display(description='Barcode Name')
    def barcode_name(self, obj):
        """Human-readable name for the related barcode."""
        b = obj.barcode_used
        if not b:
            return '-'
        if b.barcode_type == "Identification":
            return f"{b.user.username}'s identification barcode"
        if b.barcode_type == "DynamicBarcode":
            return f"Dynamic Barcode ending with {b.barcode[-4:]}"
        return f"Barcode ending with {b.barcode[-4:]}"

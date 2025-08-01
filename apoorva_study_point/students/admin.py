from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Student, Shift, Attendance, FeeTransaction, FeeConfiguration, UserProfile

# Inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fk_name = 'user'
    can_delete = False
    verbose_name_plural = 'Profile'

# Extend User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time', 'is_active']
    list_filter = ['is_active', 'name']
    ordering = ['name']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact', 'get_shifts_display', 'fee_status', 'total_due_amount', 'date_enrolled']
    list_filter = ['fee_status', 'enrolled_shifts', 'date_enrolled', 'is_active']
    search_fields = ['name', 'contact']
    filter_horizontal = ['enrolled_shifts']
    readonly_fields = ['date_enrolled', 'single_shift_fee', 'discount_applied', 'total_due_amount']
    ordering = ['name']

    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'contact', 'address')
        }),
        ('Enrollment Details', {
            'fields': ('enrolled_shifts', 'date_enrolled')
        }),
        ('Fee Information', {
            'fields': ('single_shift_fee', 'discount_applied', 'total_due_amount', 'fee_status')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Recalculate fees after saving
        obj.calculate_total_fee()
        obj.update_fee_status()

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'shift', 'date', 'status', 'marked_by', 'marked_at']
    list_filter = ['status', 'shift', 'date', 'marked_at']
    search_fields = ['student__name']
    date_hierarchy = 'date'
    ordering = ['-date', 'shift', 'student']

    def save_model(self, request, obj, form, change):
        if not obj.marked_by:
            obj.marked_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(FeeTransaction)
class FeeTransactionAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount_paid', 'payment_date', 'payment_status', 'remaining_due_after_payment', 'processed_by']
    list_filter = ['payment_status', 'payment_date', 'processed_by']
    search_fields = ['student__name', 'transaction_id']
    date_hierarchy = 'payment_date'
    readonly_fields = ['transaction_id', 'created_at', 'remaining_due_after_payment']
    ordering = ['-payment_date', '-created_at']

    fieldsets = (
        ('Transaction Details', {
            'fields': ('student', 'amount_paid', 'payment_date', 'payment_status')
        }),
        ('Processing Information', {
            'fields': ('processed_by', 'transaction_id', 'created_at')
        }),
        ('Additional Information', {
            'fields': ('remaining_due_after_payment', 'notes')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.processed_by:
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(FeeConfiguration)
class FeeConfigurationAdmin(admin.ModelAdmin):
    list_display = ['base_single_shift_fee', 'discount_two_shifts', 'discount_three_plus_shifts', 'updated_by', 'updated_at']
    readonly_fields = ['updated_at']

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        # Only allow one configuration instance
        return not FeeConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of configuration
        return False

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone_number', 'created_by', 'created_at', 'is_active']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['created_at']
    ordering = ['user__username']

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Customize admin site header
admin.site.site_header = "Apoorva Study Point Administration"
admin.site.site_title = "Apoorva Study Point Admin"
admin.site.index_title = "Welcome to Apoorva Study Point Administration"
